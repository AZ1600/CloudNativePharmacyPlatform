import json
import unittest
from unittest.mock import patch

import process_low_stock_alert_lambda


class ProcessLowStockAlertLambdaTests(unittest.TestCase):
    def test_processes_sqs_low_stock_message(self):
        event = {
            "Records": [
                {
                    "messageId": "message-001",
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
            ]
        }

        with patch.object(
            process_low_stock_alert_lambda.logger,
            "info",
        ) as mock_logger:
            result = process_low_stock_alert_lambda.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["processed_records"], 1)
        self.assertEqual(
            result["items"],
            [
                {
                    "message_id": "message-001",
                    "drug_id": "drug-001",
                }
            ],
        )
        mock_logger.assert_called_once()

    def test_handles_empty_sqs_batch(self):
        result = process_low_stock_alert_lambda.lambda_handler(
            {"Records": []},
            None,
        )

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["processed_records"], 0)
        self.assertEqual(result["items"], [])

    def test_handles_event_without_records(self):
        result = process_low_stock_alert_lambda.lambda_handler({}, None)

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["processed_records"], 0)
        self.assertEqual(result["items"], [])


if __name__ == "__main__":
    unittest.main()