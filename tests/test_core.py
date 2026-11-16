import unittest
from snowvoice_core import valid_key_shape, format_transcript, error_message


class CoreTests(unittest.TestCase):
    def test_rejects_tracking_id_and_whitespace(self):
        for value in ("", "key_example_tracking_id", " sk-" + "x" * 24, "sk-short", "sk-" + "x" * 20 + "\n"):
            self.assertFalse(valid_key_shape(value))
        self.assertTrue(valid_key_shape("sk-proj-" + "x" * 24))

    def test_punctuation_is_preserved(self):
        self.assertEqual(format_transcript("  Hello! 今天好嗎？  "), "Hello! 今天好嗎？")
        self.assertEqual(format_transcript("完成。"), "完成。")
        self.assertEqual(format_transcript("  "), "")

    def test_error_body_is_never_disclosed(self):
        class APIError(Exception):
            status_code = 401
        error = APIError("private server response")
        self.assertIn("Secret Key", error_message(error))
        self.assertNotIn("private", error_message(error))
        self.assertNotIn("private", error_message(RuntimeError("private response")))


if __name__ == "__main__":
    unittest.main()
