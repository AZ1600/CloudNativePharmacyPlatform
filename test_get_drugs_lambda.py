import importlib
import json
import os
import sys
import types
import unittest
from decimal import Decimal
from unittest.mock import Mock


MODULE_NAME = "get_drugs_lambda"


class GetDrugsLambdaTests(unittest.TestCase):
    def setUp(self):
        self.original_table_name = os.environ.get("TABLE_NAME")
        os.environ["TABLE_NAME"] = "test-inventory-table"

        self.mock_table = Mock()
        self.mock_dynamodb = Mock()
        self.mock_dynamodb.Table.return_value = self.mock_table

        sys.modules.pop(MODULE_NAME, None)

        self.original_boto3 = sys.modules.get("boto3")
        self.original_botocore = sys.modules.get("botocore")
        self.original_botocore_exceptions = sys.modules.get(
            "botocore.exceptions"
        )

        fake_boto3 = types.ModuleType("boto3")
        fake_boto3.resource = Mock(return_value=self.mock_dynamodb)

        fake_botocore = types.ModuleType("botocore")
        fake_botocore_exceptions = types.ModuleType(
            "botocore.exceptions"
        )

        class FakeClientError(Exception):
            def __init__(self, error_response, operation_name):
                super().__init__(operation_name)
                self.response = error_response
                self.operation_name = operation_name

        fake_botocore_exceptions.ClientError = FakeClientError
        fake_botocore.exceptions = fake_botocore_exceptions

        sys.modules["boto3"] = fake_boto3
        sys.modules["botocore"] = fake_botocore
        sys.modules["botocore.exceptions"] = fake_botocore_exceptions

        self.module = importlib.import_module(MODULE_NAME)

    def tearDown(self):
        if self.original_table_name is None:
            os.environ.pop("TABLE_NAME", None)
        else:
            os.environ["TABLE_NAME"] = self.original_table_name

        self.restore_module("boto3", self.original_boto3)
        self.restore_module("botocore", self.original_botocore)
        self.restore_module(
            "botocore.exceptions",
            self.original_botocore_exceptions,
        )

        sys.modules.pop(MODULE_NAME, None)

    def restore_module(self, name, module):
        if module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = module

    def api_event(self, claims=None):
        return {
            "requestContext": {
                "authorizer": {
                    "jwt": {
                        "claims": claims
                        or {
                            "custom:role": "Pharmacist",
                            "custom:hospital_id": "hospital-001",
                            "sub": "user-123",
                        }
                    }
                }
            }
        }

    def parse_response(self, result):
        self.assertIn("statusCode", result)
        self.assertIn("body", result)

        result["body"] = json.loads(result["body"])
        return result

    def inventory_item(self, drug_id, drug_name, quantity):
        return {
            "PK": "TENANT#hospital-001",
            "SK": f"DRUG#{drug_id}",
            "GSI1PK": "TENANT#hospital-001#ENTITY#DRUG",
            "GSI1SK": f"DRUG#{drug_name.upper()}#{drug_id}",
            "entity_type": "DRUG",
            "tenant_id": "hospital-001",
            "hospital_id": "hospital-001",
            "drug_id": drug_id,
            "drug_name": drug_name,
            "batch_number": f"BATCH-{drug_id}",
            "quantity": Decimal(str(quantity)),
            "reorder_level": Decimal("20"),
            "expiry_date": "2027-12-31",
            "supplier": "Example Pharmacy Supplier",
            "category": "General",
            "location": "A-01",
        }

    def test_returns_tenant_inventory(self):
        self.mock_table.query.return_value = {
            "Items": [
                self.inventory_item(
                    "drug-001",
                    "Amoxicillin 500 mg",
                    120,
                ),
                self.inventory_item(
                    "drug-002",
                    "Metformin 500 mg",
                    15,
                ),
            ]
        }

        result = self.parse_response(
            self.module.lambda_handler(self.api_event(), None)
        )

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"]["count"], 2)
        self.assertEqual(
            result["body"]["items"][0]["drug_name"],
            "Amoxicillin 500 mg",
        )
        self.assertEqual(result["body"]["items"][0]["quantity"], 120)

        self.mock_table.query.assert_called_once_with(
            IndexName="GSI1",
            KeyConditionExpression="GSI1PK = :gsi1pk",
            ExpressionAttributeValues={
                ":gsi1pk": (
                    "TENANT#hospital-001#ENTITY#DRUG"
                )
            },
        )

    def test_retrieves_all_paginated_results(self):
        first_item = self.inventory_item(
            "drug-001",
            "Amoxicillin",
            120,
        )
        second_item = self.inventory_item(
            "drug-002",
            "Metformin",
            15,
        )

        self.mock_table.query.side_effect = [
            {
                "Items": [first_item],
                "LastEvaluatedKey": {
                    "PK": "TENANT#hospital-001",
                    "SK": "DRUG#drug-001",
                },
            },
            {
                "Items": [second_item],
            },
        ]

        result = self.parse_response(
            self.module.lambda_handler(self.api_event(), None)
        )

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"]["count"], 2)
        self.assertEqual(self.mock_table.query.call_count, 2)

        second_query = self.mock_table.query.call_args_list[1].kwargs
        self.assertEqual(
            second_query["ExclusiveStartKey"],
            {
                "PK": "TENANT#hospital-001",
                "SK": "DRUG#drug-001",
            },
        )

    def test_returns_empty_inventory(self):
        self.mock_table.query.return_value = {"Items": []}

        result = self.parse_response(
            self.module.lambda_handler(self.api_event(), None)
        )

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"], {"items": [], "count": 0})

    def test_allows_read_only_viewer(self):
        self.mock_table.query.return_value = {"Items": []}

        event = self.api_event(
            {
                "custom:role": "Viewer",
                "custom:hospital_id": "hospital-001",
                "sub": "viewer-123",
            }
        )

        result = self.parse_response(
            self.module.lambda_handler(event, None)
        )

        self.assertEqual(result["statusCode"], 200)
        self.mock_table.query.assert_called_once()

    def test_rejects_unauthorized_role(self):
        event = self.api_event(
            {
                "custom:role": "ExternalUser",
                "custom:hospital_id": "hospital-001",
                "sub": "external-123",
            }
        )

        result = self.parse_response(
            self.module.lambda_handler(event, None)
        )

        self.assertEqual(result["statusCode"], 403)
        self.assertEqual(
            result["body"]["message"],
            "Unauthorized",
        )
        self.mock_table.query.assert_not_called()

    def test_rejects_missing_tenant_identifier(self):
        event = self.api_event(
            {
                "custom:role": "Pharmacist",
                "sub": "user-123",
            }
        )

        result = self.parse_response(
            self.module.lambda_handler(event, None)
        )

        self.assertEqual(result["statusCode"], 400)
        self.assertIn(
            "Missing tenant identifier",
            result["body"]["message"],
        )
        self.mock_table.query.assert_not_called()


if __name__ == "__main__":
    unittest.main()