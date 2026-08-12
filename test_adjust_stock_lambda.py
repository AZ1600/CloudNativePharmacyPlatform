import importlib
import json
import os
import sys
import types
import unittest
from unittest.mock import Mock


MODULE_NAME = "adjust_stock_lambda"


class AdjustStockLambdaTests(unittest.TestCase):
    def setUp(self):
        self.original_table_name = os.environ.get("TABLE_NAME")
        os.environ["TABLE_NAME"] = "test-inventory-table"
        self.mock_table = Mock()
        self.mock_table.name = "test-inventory-table"
        self.mock_table.get_item.return_value = {
            "Item": {
                "PK": "TENANT#hospital-001",
                "SK": "DRUG#drug-001",
                "drug_id": "drug-001",
                "drug_name": "Amoxicillin 500 mg",
                "batch_number": "AMX-001",
                "quantity": 20,
            }
        }
        self.mock_resource = Mock()
        self.mock_resource.Table.return_value = self.mock_table
        self.mock_client = Mock()

        self.original_modules = {
            name: sys.modules.get(name)
            for name in (
                "boto3",
                "boto3.dynamodb",
                "boto3.dynamodb.types",
                "botocore",
                "botocore.exceptions",
            )
        }
        sys.modules.pop(MODULE_NAME, None)

        fake_boto3 = types.ModuleType("boto3")
        fake_boto3.resource = Mock(return_value=self.mock_resource)
        fake_boto3.client = Mock(return_value=self.mock_client)

        class FakeTypeSerializer:
            def serialize(self, value):
                if isinstance(value, str):
                    return {"S": value}
                return {"N": str(value)}

        fake_boto3_dynamodb = types.ModuleType("boto3.dynamodb")
        fake_boto3_types = types.ModuleType("boto3.dynamodb.types")
        fake_boto3_types.TypeSerializer = FakeTypeSerializer
        fake_boto3_dynamodb.types = fake_boto3_types
        fake_boto3.dynamodb = fake_boto3_dynamodb

        fake_botocore = types.ModuleType("botocore")
        fake_exceptions = types.ModuleType("botocore.exceptions")

        class FakeClientError(Exception):
            def __init__(self, error_response, operation_name):
                super().__init__(operation_name)
                self.response = error_response

        fake_exceptions.ClientError = FakeClientError
        fake_botocore.exceptions = fake_exceptions
        sys.modules["boto3"] = fake_boto3
        sys.modules["boto3.dynamodb"] = fake_boto3_dynamodb
        sys.modules["boto3.dynamodb.types"] = fake_boto3_types
        sys.modules["botocore"] = fake_botocore
        sys.modules["botocore.exceptions"] = fake_exceptions
        self.module = importlib.import_module(MODULE_NAME)

    def tearDown(self):
        if self.original_table_name is None:
            os.environ.pop("TABLE_NAME", None)
        else:
            os.environ["TABLE_NAME"] = self.original_table_name
        for name, module in self.original_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
        sys.modules.pop(MODULE_NAME, None)

    def event(self, adjustment_type, quantity, role="Pharmacist"):
        return {
            "pathParameters": {"drug_id": "drug-001"},
            "body": json.dumps(
                {
                    "adjustment_type": adjustment_type,
                    "quantity": quantity,
                    "reason": "Approved stock operation",
                }
            ),
            "requestContext": {
                "authorizer": {
                    "jwt": {
                        "claims": {
                            "custom:role": role,
                            "custom:hospital_id": "hospital-001",
                            "sub": "user-123",
                        }
                    }
                }
            },
        }

    def parse(self, result):
        result["body"] = json.loads(result["body"])
        return result

    def test_receipt_adds_stock_and_writes_audit_record_atomically(self):
        result = self.parse(self.module.lambda_handler(self.event("RECEIPT", 10), None))

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"]["previous_quantity"], 20)
        self.assertEqual(result["body"]["new_quantity"], 30)
        transaction = self.mock_client.transact_write_items.call_args.kwargs
        self.assertEqual(len(transaction["TransactItems"]), 2)
        audit_item = transaction["TransactItems"][1]["Put"]["Item"]
        self.assertEqual(audit_item["quantity_change"], {"N": "10"})

    def test_dispense_subtracts_stock(self):
        result = self.parse(self.module.lambda_handler(self.event("DISPENSE", 5), None))

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"]["new_quantity"], 15)
        self.assertEqual(result["body"]["quantity_change"], -5)

    def test_quarantine_cannot_make_stock_negative(self):
        result = self.parse(
            self.module.lambda_handler(self.event("QUARANTINE", 21), None)
        )

        self.assertEqual(result["statusCode"], 409)
        self.mock_client.transact_write_items.assert_not_called()

    def test_correction_accepts_a_negative_difference(self):
        result = self.parse(
            self.module.lambda_handler(self.event("CORRECTION", -3), None)
        )

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"]["new_quantity"], 17)

    def test_viewer_cannot_adjust_stock(self):
        result = self.parse(
            self.module.lambda_handler(self.event("RECEIPT", 10, role="Viewer"), None)
        )

        self.assertEqual(result["statusCode"], 403)
        self.mock_table.get_item.assert_not_called()

    def test_missing_medicine_returns_not_found(self):
        self.mock_table.get_item.return_value = {}
        result = self.parse(self.module.lambda_handler(self.event("RECEIPT", 10), None))

        self.assertEqual(result["statusCode"], 404)
        self.mock_client.transact_write_items.assert_not_called()


if __name__ == "__main__":
    unittest.main()
