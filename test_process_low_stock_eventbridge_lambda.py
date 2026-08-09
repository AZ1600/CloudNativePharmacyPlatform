import unittest
from unittest.mock import patch

import process_low_stock_eventbridge_lambda


class ProcessLowStockEventBridgeLambdaTests(unittest.TestCase):
    def test_processes_eventbridge_low_stock_event(self):
        event = {
            "source": "pharmacy.inventory",
            "detail-type": "LowStockDetected",
            "detail": {
                "event_type": "LOW_STOCK_DETECTED",
                "tenant_id": "tenant-001",
                "drug_id": "drug-001",
                "drug_name": "Amoxicillin",
                "quantity": 10,
                "reorder_level": 20,
            },
        }

        with patch.object(
            process_low_stock_eventbridge_lambda.logger,
            "info",
        ) as mock_logger:
            result = process_low_stock_eventbridge_lambda.lambda_handler(
                event,
                None,
            )

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["processed_records"], 1)
        self.assertEqual(
            result["item"],
            {
                "drug_id": "drug-001",
                "tenant_id": "tenant-001",
            },
        )
        mock_logger.assert_called_once()

    def test_handles_event_without_detail(self):
        result = process_low_stock_eventbridge_lambda.lambda_handler(
            {},
            None,
        )

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["processed_records"], 1)
        self.assertEqual(
            result["item"],
            {
                "drug_id": None,
                "tenant_id": None,
            },
        )

    def test_handles_partial_event_detail(self):
        event = {
            "detail": {
                "tenant_id": "tenant-002",
                "drug_id": "drug-002",
            }
        }

        result = process_low_stock_eventbridge_lambda.lambda_handler(
            event,
            None,
        )

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["item"]["tenant_id"], "tenant-002")
        self.assertEqual(result["item"]["drug_id"], "drug-002")


if __name__ == "__main__":
    unittest.main()