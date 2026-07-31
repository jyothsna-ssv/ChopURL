import unittest

from pydantic import ValidationError

from app.models.schemas import URLRequest


class URLRequestSchemaTest(unittest.TestCase):
    def test_non_string_custom_code_returns_validation_error(self):
        with self.assertRaises(ValidationError):
            URLRequest.model_validate({"url": "https://example.com", "custom_code": 123})

    def test_custom_code_with_outer_whitespace_is_rejected(self):
        with self.assertRaisesRegex(ValidationError, "leading or trailing whitespace"):
            URLRequest.model_validate({"url": "https://example.com", "custom_code": " launch "})


if __name__ == "__main__":
    unittest.main()
