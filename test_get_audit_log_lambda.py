import importlib
import json
import os
import sys
import types
import unittest
from decimal import Decimal
from unittest.mock import Mock


MODULE_NAME = "get_audit_log_lambda"


class GetAuditLogLambdaTests(unittest.TestCase):
    def setUp(self):
        self.original_table_name = os.environ.get("TABLE_NAME")
        os.environ["TABLE_NAME"] = "test-inventory-table"
        self.mock_table = Mock()
        self.mock_resource = Mock()
        self.mock_resource.Table.return_value = self.mock_table
        self.original_modules = {
            name: sys.modules.get(name)
            for name in ("boto3", "botocore", "botocore.exceptions")
        }
        sys.modules.pop(MODULE_NAME, None)

        fake_boto3 = types.ModuleType("boto3")
        fake_boto3.resource = Mock(return_value=self.mock_resource)
        fake_botocore = types.ModuleType("botocore")
        fake_exceptions = types.ModuleType("botocore.exceptions")

        class FakeClientError(Exception):
            pass

        fake_exceptions.ClientError = FakeClientError
        fake_botocore.exceptions = fake_exceptions
        sys.modules["boto3"] = fake_boto3
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

    def event(self, role="Viewer"):
        return {
            "requestContext": {
                "authorizer": {
                    "jwt": {
                        "claims": {
                            "custom:role": role,
                            "custom:hospital_id": "hospital-001",
                            "sub": "viewer-123",
                        }
                    }
                }
            }
        }

    def parse(self, result):
        result["body"] = json.loads(result["body"])
        return result

    def test_returns_tenant_audit_history_newest_first(self):
        self.mock_table.query.return_value = {
            "Items": [
                {
                    "adjustment_id": "audit-001",
                    "drug_id": "drug-001",
                    "drug_name": "Amoxicillin",
                    "batch_number": "AMX-001",
                    "adjustment_type": "RECEIPT",
                    "quantity_change": Decimal("10"),
                    "previous_quantity": Decimal("20"),
                    "new_quantity": Decimal("30"),
                    "reason": "Delivery received",
                    "created_at": "2026-08-12T12:00:00+00:00",
                    "created_by": "user-123",
                }
            ]
        }

        result = self.parse(self.module.lambda_handler(self.event(), None))

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"]["items"][0]["id"], "audit-001")
        self.mock_table.query.assert_called_once_with(
            IndexName="GSI1",
            KeyConditionExpression="GSI1PK = :gsi1pk",
            ExpressionAttributeValues={
                ":gsi1pk": "TENANT#hospital-001#ENTITY#AUDIT"
            },
            ScanIndexForward=False,
            Limit=100,
        )

    def test_returns_empty_history(self):
        self.mock_table.query.return_value = {"Items": []}
        result = self.parse(self.module.lambda_handler(self.event(), None))
        self.assertEqual(result["body"], {"items": [], "count": 0})

    def test_rejects_unknown_role(self):
        result = self.parse(self.module.lambda_handler(self.event("ExternalUser"), None))
        self.assertEqual(result["statusCode"], 403)
        self.mock_table.query.assert_not_called()


if __name__ == "__main__":
    unittest.main()
