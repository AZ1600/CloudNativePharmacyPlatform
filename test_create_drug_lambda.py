import importlib
import json
import os
import sys
import types
import unittest
from unittest.mock import Mock, patch


MODULE_NAME = "create_drug_lambda"


class CreateDrugLambdaTests(unittest.TestCase):
    def setUp(self):
        self.original_table_name = os.environ.get("TABLE_NAME")
        self.original_queue_url = os.environ.get("LOW_STOCK_QUEUE_URL")
        self.original_topic_arn = os.environ.get("LOW_STOCK_TOPIC_ARN")
        self.original_stream_name = os.environ.get("LOW_STOCK_STREAM_NAME")
        self.original_event_bus_name = os.environ.get("EVENT_BUS_NAME")

        os.environ["TABLE_NAME"] = "test-inventory-table"
        os.environ["LOW_STOCK_QUEUE_URL"] = "https://sqs.eu-west-1.amazonaws.com/123/low-stock"
        os.environ["LOW_STOCK_TOPIC_ARN"] = "arn:aws:sns:eu-west-1:123456789012:low-stock"
        os.environ["LOW_STOCK_STREAM_NAME"] = "low-stock-stream"
        os.environ["EVENT_BUS_NAME"] = "default"

        self.mock_table = Mock()
        self.mock_dynamodb = Mock()
        self.mock_dynamodb.Table.return_value = self.mock_table
        self.mock_sqs = Mock()
        self.mock_sns = Mock()
        self.mock_kinesis = Mock()
        self.mock_events = Mock()
        self.mock_events.put_events.return_value = {"FailedEntryCount": 0, "Entries": [{}]}

        sys.modules.pop(MODULE_NAME, None)
        self.original_boto3 = sys.modules.get("boto3")
        self.original_botocore = sys.modules.get("botocore")
        self.original_botocore_exceptions = sys.modules.get("botocore.exceptions")

        fake_boto3 = types.ModuleType("boto3")
        fake_boto3.resource = Mock(return_value=self.mock_dynamodb)
        fake_boto3.client = Mock(side_effect=self.mock_boto3_client)

        fake_botocore = types.ModuleType("botocore")
        fake_botocore_exceptions = types.ModuleType("botocore.exceptions")

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
        self.restore_env("TABLE_NAME", self.original_table_name)
        self.restore_env("LOW_STOCK_QUEUE_URL", self.original_queue_url)
        self.restore_env("LOW_STOCK_TOPIC_ARN", self.original_topic_arn)
        self.restore_env("LOW_STOCK_STREAM_NAME", self.original_stream_name)
        self.restore_env("EVENT_BUS_NAME", self.original_event_bus_name)
        self.restore_module("boto3", self.original_boto3)
        self.restore_module("botocore", self.original_botocore)
        self.restore_module("botocore.exceptions", self.original_botocore_exceptions)
        sys.modules.pop(MODULE_NAME, None)

    def restore_env(self, key, value):
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

    def restore_module(self, name, module):
        if module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = module

    def mock_boto3_client(self, service_name, *args, **kwargs):
        if service_name == "sqs":
            return self.mock_sqs
        if service_name == "sns":
            return self.mock_sns
        if service_name == "kinesis":
            return self.mock_kinesis
        if service_name == "events":
            return self.mock_events
        raise AssertionError(f"Unexpected boto3 client request: {service_name}")

    def api_event(self, body, claims=None):
        return {
            "body": json.dumps(body),
            "requestContext": {
                "authorizer": {
                    "jwt": {
                        "claims": claims
                        or {
                            "custom:role": "HospitalAdmin",
                            "custom:hospital_id": "hosp_001",
                            "sub": "user-123",
                        }
                    }
                }
            },
        }

    def parse_response(self, response):
        self.assertIn("statusCode", response)
        self.assertIn("body", response)
        response["body"] = json.loads(response["body"])
        return response

    def test_creates_drug_and_publishes_events_when_stock_is_low(self):
        event = self.api_event(
            {
                "drug_name": "Amoxicillin",
                "batch_number": "BATCH-LOW-001",
                "quantity": 10,
                "reorder_level": 20,
                "expiry_date": "2027-12-31",
                "supplier": "Acme Pharma",
            }
        )

        response = self.parse_response(self.module.lambda_handler(event, None))

        self.assertEqual(response["statusCode"], 201)
        self.assertEqual(response["body"]["message"], "Drug created")
        self.assertTrue(response["body"]["low_stock_event_sent"])
        self.assertTrue(response["body"]["sns_event_sent"])
        self.assertTrue(response["body"]["eventbridge_event_sent"])
        self.assertTrue(response["body"]["kinesis_event_sent"])
        self.mock_table.put_item.assert_called_once()
        self.mock_sqs.send_message.assert_called_once()
        self.mock_sns.publish.assert_called_once()
        self.mock_events.put_events.assert_called_once()
        self.mock_kinesis.put_record.assert_called_once()

    def test_creates_drug_without_events_when_stock_is_healthy(self):
        event = self.api_event(
            {
                "drug_name": "Paracetamol",
                "batch_number": "BATCH-001",
                "quantity": 150,
                "reorder_level": 20,
                "expiry_date": "2027-12-31",
                "supplier": "Acme Pharma",
            }
        )

        response = self.parse_response(self.module.lambda_handler(event, None))

        self.assertEqual(response["statusCode"], 201)
        self.assertFalse(response["body"]["low_stock_event_sent"])
        self.assertFalse(response["body"]["sns_event_sent"])
        self.assertFalse(response["body"]["eventbridge_event_sent"])
        self.assertFalse(response["body"]["kinesis_event_sent"])
        self.mock_table.put_item.assert_called_once()
        self.mock_sqs.send_message.assert_not_called()
        self.mock_sns.publish.assert_not_called()
        self.mock_events.put_events.assert_not_called()
        self.mock_kinesis.put_record.assert_not_called()

    def test_returns_400_when_required_fields_are_missing(self):
        event = self.api_event(
            {
                "drug_name": "Paracetamol",
                "batch_number": "BATCH-001",
                "quantity": 150,
            }
        )

        response = self.parse_response(self.module.lambda_handler(event, None))

        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Missing required fields", response["body"]["message"])
        self.mock_table.put_item.assert_not_called()

    def test_returns_403_for_unauthorized_role(self):
        event = self.api_event(
            {
                "drug_name": "Paracetamol",
                "batch_number": "BATCH-001",
                "quantity": 150,
                "reorder_level": 20,
                "expiry_date": "2027-12-31",
            },
            claims={
                "custom:role": "Viewer",
                "custom:hospital_id": "hosp_001",
                "sub": "user-123",
            },
        )

        response = self.parse_response(self.module.lambda_handler(event, None))

        self.assertEqual(response["statusCode"], 403)
        self.assertEqual(response["body"]["message"], "Unauthorized")
        self.mock_table.put_item.assert_not_called()


if __name__ == "__main__":
    unittest.main()
