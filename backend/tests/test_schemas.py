import unittest

from pydantic import ValidationError

from app.models.schemas import URLRequest


class URLRequestSchemaTest(unittest.TestCase):
    def test_non_string_custom_code_returns_validation_error(self):
        with self.assertRaises(ValidationError):
            URLRequest.model_validate({"url": "https://example.com", "custom_code": 123})


if __name__ == "__main__":
    unittest.main()
