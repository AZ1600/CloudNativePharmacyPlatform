import json
import unittest
from unittest.mock import patch

import process_low_stock_alert_lambda


class ProcessLowStockAlertLambdaTests(unittest.TestCase):
    def valid_record(self, message_id="message-001"):
        return {
            "messageId": message_id,
            "body": json.dumps(
                {
                    "event_type": "LOW_STOCK_DETECTED",
                    "tenant_id": "tenant-001",
                    "drug_id": "drug-001",
                    "drug_name": "Amoxicillin",
                    "quantity": 10,
                    "reorder_level": 20,
                }
            ),
        }

    def test_processes_valid_sqs_message(self):
        event = {
            "Records": [
                self.valid_record(),
            ]
        }

        with patch.object(
            process_low_stock_alert_lambda.logger,
            "info",
        ) as mock_logger:
            result = process_low_stock_alert_lambda.lambda_handler(
                event,
                None,
            )

        self.assertEqual(result, {"batchItemFailures": []})
        mock_logger.assert_called_once()

    def test_handles_empty_sqs_batch(self):
        result = process_low_stock_alert_lambda.lambda_handler(
            {"Records": []},
            None,
        )

        self.assertEqual(result, {"batchItemFailures": []})

    def test_returns_only_failed_message_from_mixed_batch(self):
        event = {
            "Records": [
                self.valid_record("message-valid"),
                {
                    "messageId": "message-invalid",
                    "body": "not-valid-json",
                },
            ]
        }

        with (
            patch.object(
                process_low_stock_alert_lambda.logger,
                "info",
            ) as mock_info,
            patch.object(
                process_low_stock_alert_lambda.logger,
                "exception",
            ) as mock_exception,
        ):
            result = process_low_stock_alert_lambda.lambda_handler(
                event,
                None,
            )

        self.assertEqual(
            result,
            {
                "batchItemFailures": [
                    {
                        "itemIdentifier": "message-invalid",
                    }
                ]
            },
        )
        mock_info.assert_called_once()
        mock_exception.assert_called_once()

    def test_returns_failure_when_record_body_is_missing(self):
        event = {
            "Records": [
                {
                    "messageId": "message-missing-body",
                }
            ]
        }

        result = process_low_stock_alert_lambda.lambda_handler(
            event,
            None,
        )

        self.assertEqual(
            result,
            {
                "batchItemFailures": [
                    {
                        "itemIdentifier": "message-missing-body",
                    }
                ]
            },
        )


if __name__ == "__main__":
    unittest.main()