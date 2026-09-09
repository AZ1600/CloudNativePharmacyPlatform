from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent

LAMBDA_FILES = (
    "adjust_stock_lambda.py",
    "create_drug_lambda.py",
    "get_audit_log_lambda.py",
    "get_drugs_lambda.py",
)


class CorsConfigurationTests(unittest.TestCase):
    def test_api_gateway_uses_explicit_allowed_origin(self):
        template = (ROOT / "template.yaml").read_text()

        self.assertIn("AllowedOrigin:", template)
        self.assertIn("- !Ref AllowedOrigin", template)
        self.assertNotIn(
            'AllowOrigins:\n          - "*"',
            template,
        )

    def test_lambda_responses_do_not_define_cors_headers(self):
        for filename in LAMBDA_FILES:
            source = (ROOT / filename).read_text()

            with self.subTest(filename=filename):
                self.assertNotIn(
                    "Access-Control-Allow-Origin",
                    source,
                )
                self.assertNotIn(
                    "Access-Control-Allow-Headers",
                    source,
                )
                self.assertNotIn(
                    "Access-Control-Allow-Methods",
                    source,
                )

    def test_pipeline_passes_allowed_origin_to_sam(self):
        pipeline = (ROOT / "pipeline-template.yaml").read_text()
        buildspec = (ROOT / "buildspec.yml").read_text()

        self.assertIn("AllowedOrigin:", pipeline)
        self.assertIn("ALLOWED_ORIGIN", pipeline)
        self.assertIn(
            'AllowedOrigin="$ALLOWED_ORIGIN"',
            buildspec,
        )


if __name__ == "__main__":
    unittest.main()
