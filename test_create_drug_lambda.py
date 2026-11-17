import importlib
import json
import os
import sys
import types
import unittest
from unittest.mock import Mock


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
        self.mock_dynamodb_client = Mock()
        self.mock_table.name = "test-inventory-table"
        self.mock_sqs = Mock()
        self.mock_sns = Mock()
        self.mock_kinesis = Mock()
        self.mock_events = Mock()
        self.mock_events.put_events.return_value = {"FailedEntryCount": 0, "Entries": [{}]}

        sys.modules.pop(MODULE_NAME, None)
        self.original_boto3 = sys.modules.get("boto3")
        self.original_boto3_dynamodb = sys.modules.get("boto3.dynamodb")
        self.original_boto3_types = sys.modules.get("boto3.dynamodb.types")
        self.original_botocore = sys.modules.get("botocore")
        self.original_botocore_exceptions = sys.modules.get("botocore.exceptions")

        fake_boto3 = types.ModuleType("boto3")
        fake_boto3.resource = Mock(return_value=self.mock_dynamodb)
        fake_boto3.client = Mock(side_effect=self.mock_boto3_client)

        class FakeTypeSerializer:
            def serialize(self, value):
                if value is None:
                    return {"NULL": True}
                if isinstance(value, str):
                    return {"S": value}
                if isinstance(value, (int, float)):
                    return {"N": str(value)}
                raise AssertionError(f"Unexpected DynamoDB value: {value!r}")

        fake_dynamodb_module = types.ModuleType("boto3.dynamodb")
        fake_types_module = types.ModuleType("boto3.dynamodb.types")
        fake_types_module.TypeSerializer = FakeTypeSerializer
        fake_dynamodb_module.types = fake_types_module
        fake_boto3.dynamodb = fake_dynamodb_module

        fake_botocore = types.ModuleType("botocore")
        fake_botocore_exceptions = types.ModuleType("botocore.exceptions")

        class FakeClientError(Exception):
            def __init__(self, error_response, operation_name):
                super().__init__(operation_name)
                self.response = error_response
                self.operation_name = operation_name

        fake_botocore_exceptions.ClientError = FakeClientError
        fake_botocore.exceptions = fake_botocore_exceptions
        self.fake_client_error = FakeClientError

        sys.modules["boto3.dynamodb"] = fake_dynamodb_module
        sys.modules["boto3.dynamodb.types"] = fake_types_module
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
        self.restore_module("boto3.dynamodb", self.original_boto3_dynamodb)
        self.restore_module("boto3.dynamodb.types", self.original_boto3_types)
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
        if service_name == "dynamodb":
            return self.mock_dynamodb_client
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
        self.mock_dynamodb_client.transact_write_items.assert_called_once()
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
        self.mock_dynamodb_client.transact_write_items.assert_called_once()
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
        self.mock_dynamodb_client.transact_write_items.assert_not_called()

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
        self.mock_dynamodb_client.transact_write_items.assert_not_called()

    def test_rejects_invalid_expiry_date(self):
        event = self.api_event(
            {
                "drug_name": "Paracetamol",
                "batch_number": "BATCH-001",
                "quantity": 150,
                "reorder_level": 20,
                "expiry_date": "not-a-date",
            }
        )

        response = self.parse_response(self.module.lambda_handler(event, None))

        self.assertEqual(response["statusCode"], 400)
        self.assertIn("YYYY-MM-DD", response["body"]["message"])
        self.mock_dynamodb_client.transact_write_items.assert_not_called()

    def test_rejects_non_integer_quantity(self):
        event = self.api_event(
            {
                "drug_name": "Paracetamol",
                "batch_number": "BATCH-001",
                "quantity": 10.5,
                "reorder_level": 20,
                "expiry_date": "2027-12-31",
            }
        )

        response = self.parse_response(self.module.lambda_handler(event, None))

        self.assertEqual(response["statusCode"], 400)
        self.assertIn("whole number", response["body"]["message"])
        self.mock_dynamodb_client.transact_write_items.assert_not_called()


    def test_atomic_transaction_creates_medicine_and_uniqueness_guard(self):
        body = {
            "drug_name": "Amoxicillin",
            "batch_number": "AMX-001",
            "quantity": 100,
            "reorder_level": 10,
            "expiry_date": "2027-12-31",
        }
        result = self.parse_response(self.module.lambda_handler(self.api_event(body), None))
        self.assertEqual(result["statusCode"], 201)
        transaction = self.mock_dynamodb_client.transact_write_items.call_args.kwargs
        puts = [operation["Put"] for operation in transaction["TransactItems"]]
        self.assertEqual(len(puts), 2)
        self.assertTrue(all(p["TableName"] == "test-inventory-table" for p in puts))
        self.assertTrue(all("attribute_not_exists" in p["ConditionExpression"] for p in puts))
        self.assertEqual(puts[0]["Item"]["SK"]["S"].startswith("DRUG#"), True)
        self.assertEqual(puts[1]["Item"]["SK"]["S"].startswith("BATCH#"), True)
        self.assertEqual(puts[1]["Item"]["PK"], puts[0]["Item"]["PK"])
        self.assertNotIn("GSI1PK", puts[1]["Item"])

    def test_rejects_duplicate_batch_without_publishing(self):
        self.mock_dynamodb_client.transact_write_items.side_effect = (
            self.fake_client_error(
                {
                    "Error": {"Code": "TransactionCanceledException"},
                    "CancellationReasons": [
                        {"Code": "None"},
                        {"Code": "ConditionalCheckFailed"},
                    ],
                },
                "TransactWriteItems",
            )
        )
        event = self.api_event({
            "drug_name": "Amoxicillin",
            "batch_number": "AMX-001",
            "quantity": 2,
            "reorder_level": 10,
            "expiry_date": "2027-12-31",
        })
        result = self.parse_response(self.module.lambda_handler(event, None))
        self.assertEqual(result["statusCode"], 409)
        self.assertIn("already exists", result["body"]["message"])
        self.mock_sqs.send_message.assert_not_called()
        self.mock_sns.publish.assert_not_called()
        self.mock_kinesis.put_record.assert_not_called()
        self.mock_events.put_events.assert_not_called()

    def test_guard_is_case_insensitive_for_name_and_batch(self):
        first = self.module.batch_uniqueness_key(" Amoxicillin ", "amx-001")
        second = self.module.batch_uniqueness_key("AMOXICILLIN", " AMX-001 ")
        self.assertEqual(first, second)
        self.assertNotEqual(first, self.module.batch_uniqueness_key("Metformin", "AMX-001"))

    def test_same_batch_can_exist_in_different_tenants(self):
        body = {
            "drug_name": "Amoxicillin",
            "batch_number": "AMX-001",
            "quantity": 100,
            "reorder_level": 10,
            "expiry_date": "2027-12-31",
        }
        self.module.lambda_handler(self.api_event(body), None)
        other_tenant = {
            "custom:role": "Pharmacist",
            "custom:hospital_id": "hosp_002",
            "sub": "user-456",
        }
        self.module.lambda_handler(self.api_event(body, claims=other_tenant), None)
        calls = self.mock_dynamodb_client.transact_write_items.call_args_list
        self.assertEqual(len(calls), 2)
        guards = [call.kwargs["TransactItems"][1]["Put"]["Item"] for call in calls]
        self.assertNotEqual(guards[0]["PK"], guards[1]["PK"])
        self.assertEqual(guards[0]["SK"], guards[1]["SK"])

    def test_transaction_cancellation_without_duplicate_is_server_error(self):
        self.mock_dynamodb_client.transact_write_items.side_effect = (
            self.fake_client_error(
                {
                    "Error": {"Code": "TransactionCanceledException"},
                    "CancellationReasons": [{"Code": "TransactionConflict"}],
                },
                "TransactWriteItems",
            )
        )
        body = {
            "drug_name": "Amoxicillin",
            "batch_number": "AMX-001",
            "quantity": 100,
            "reorder_level": 10,
            "expiry_date": "2027-12-31",
        }
        result = self.parse_response(self.module.lambda_handler(self.api_event(body), None))
        self.assertEqual(result["statusCode"], 500)

    def test_rejects_non_string_medicine_names_before_writing(self):
        for name in (None, 123, True, {"malformed": "object"}):
            with self.subTest(name=name):
                event = self.api_event({
                    "drug_name": name,
                    "batch_number": "AMX-001",
                    "quantity": 100,
                    "reorder_level": 10,
                    "expiry_date": "2027-12-31",
                })
                result = self.parse_response(self.module.lambda_handler(event, None))
                self.assertEqual(result["statusCode"], 400)
                self.mock_dynamodb_client.transact_write_items.assert_not_called()


if __name__ == "__main__":
    unittest.main()
