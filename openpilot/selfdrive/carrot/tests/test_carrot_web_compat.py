import unittest

from openpilot.selfdrive.carrot.carrot_web_compat import validated_payload


class TestCarrotWebCompat(unittest.TestCase):
  def test_validated_payload_filters_unknown_fields(self):
    self.assertEqual(validated_payload({"desiredSpeed": 80, "unknown": "ignored"}), {"desiredSpeed": 80})

  def test_validated_payload_rejects_invalid_integer(self):
    with self.assertRaises((TypeError, ValueError)):
      validated_payload({"desiredSpeed": "fast"})

  def test_validated_payload_rejects_long_text(self):
    with self.assertRaises(ValueError):
      validated_payload({"remote": "x" * 513})
