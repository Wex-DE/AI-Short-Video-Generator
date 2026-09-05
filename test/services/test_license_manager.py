import unittest
from unittest.mock import patch

from app.services import license_manager


class TestLicenseManager(unittest.TestCase):
    def test_get_device_id_format(self):
        dev_id = license_manager.get_device_id()
        self.assertTrue(dev_id.startswith("0X") or dev_id.startswith("0x"))
        self.assertGreaterEqual(len(dev_id), 8)

    def test_parse_verification_text(self):
        sample = """
        # Test verification list
        0x1122334455, 30d, verified
        0xAABBCCDDEE, 60d, ban
        0x9988776655, 2026-12-31, verified
        """
        records = license_manager.parse_verification_text(sample)
        self.assertIn("0X1122334455", records)
        self.assertEqual(records["0X1122334455"]["status"], "verified")
        self.assertEqual(records["0X1122334455"]["plan"], "30d")
        self.assertEqual(records["0XAABBCCDDEE"]["status"], "ban")

    def test_verify_active_device(self):
        dev_id = license_manager.get_device_id()
        mock_content = f"{dev_id}, 30d, verified"
        result = license_manager.check_device_license(custom_content=mock_content)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.status, license_manager.LicenseStatus.ACTIVE)
        self.assertIsNotNone(result.days_remaining)
        self.assertGreater(result.days_remaining, 0)

    def test_verify_banned_device(self):
        dev_id = license_manager.get_device_id()
        mock_content = f"{dev_id}, 30d, ban"
        result = license_manager.check_device_license(custom_content=mock_content)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.status, license_manager.LicenseStatus.BANNED)

    def test_verify_unregistered_device(self):
        mock_content = "0X0000000000, 30d, verified"
        result = license_manager.check_device_license(custom_content=mock_content)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.status, license_manager.LicenseStatus.UNVERIFIED)


if __name__ == "__main__":
    unittest.main()
