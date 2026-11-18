"""
DLP ve Sanitizer Testleri
"""

import unittest
from gateway.sanitizer import PIISanitizer

class TestPIISanitizer(unittest.TestCase):
    def setUp(self):
        self.sanitizer = PIISanitizer()

    def test_email_sanitization(self):
        text = "Lütfen raporu ahmet.yilmaz@kurum.gov.tr adresine iletin."
        clean, reds = self.sanitizer.sanitize(text)
        self.assertIn("[MASKE_EMAIL", clean)
        self.assertNotIn("ahmet.yilmaz@kurum.gov.tr", clean)
        self.assertEqual(len(reds), 1)
        self.assertEqual(reds[0]["type"], "EMAIL")

    def test_api_key_sanitization(self):
        text = "OpenAI key: sk-abcdef1234567890abcdef1234567890 ve AWS: AKIAIOSFODNN7EXAMPLE"
        clean, reds = self.sanitizer.sanitize(text)
        self.assertIn("[MASKE_GİZLİ_ANAHTAR]", clean)
        self.assertNotIn("sk-abcdef1234567890abcdef1234567890", clean)
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", clean)
        self.assertEqual(len(reds), 2)

    def test_iban_sanitization(self):
        text = "Havale için IBAN: TR33 0006 1005 1978 6451 2345 01"
        clean, reds = self.sanitizer.sanitize(text)
        self.assertIn("[MASKE_IBAN]", clean)
        self.assertNotIn("TR33 0006", clean)
        self.assertEqual(len(reds), 1)

    def test_phone_sanitization(self):
        text = "Bana 0532 123 45 67 veya +905559876543 üzerinden ulaşın."
        clean, reds = self.sanitizer.sanitize(text)
        self.assertIn("[MASKE_TELEFON]", clean)
        self.assertNotIn("0532 123 45 67", clean)

    def test_tckn_luhn_algorithm(self):
        # Geçersiz TCKN (rastgele 11 hane ama algoritmayı tutturamaz)
        invalid_tckn = "11111111111"
        self.assertFalse(self.sanitizer.is_valid_tckn(invalid_tckn))

        # Geçerli TCKN testi (10000000146 -> 10.hane=4, 11.hane=6)
        valid_tckn = "10000000146"
        self.assertTrue(self.sanitizer.is_valid_tckn(valid_tckn))

        text_with_fake = "Müşteri no: 11111111111 kayıtlıdır."
        clean, reds = self.sanitizer.sanitize(text_with_fake)
        # Geçersiz olduğu için TCKN maskelenmemeli (false positive önleme)
        self.assertEqual(len([r for r in reds if r["type"] == "TCKN"]), 0)

        text_with_valid = "Müşteri TCKN: 10000000146 onaylandı."
        clean_v, reds_v = self.sanitizer.sanitize(text_with_valid)
        self.assertIn("[MASKE_TCKN]", clean_v)
        self.assertEqual(len([r for r in reds_v if r["type"] == "TCKN"]), 1)

    def test_tr_iban_mod97(self):
        valid_iban = "TR33 0006 1005 1978 6457 8413 26"
        self.assertTrue(self.sanitizer.is_valid_tr_iban(valid_iban))
        invalid_iban = "TR00 0006 1005 1978 6457 8413 99"
        self.assertFalse(self.sanitizer.is_valid_tr_iban(invalid_iban))

    def test_internal_ip_and_mac_sanitization(self):
        text = "Sunucu 192.168.1.45 ve 10.24.0.12 adreslerinde, MAC: 00:1A:2B:3C:4D:5E ile çalışıyor."
        clean, reds = self.sanitizer.sanitize(text)
        self.assertIn("[MASKE_İÇ_İP]", clean)
        self.assertIn("[MASKE_MAC_ADRESİ]", clean)
        self.assertNotIn("192.168.1.45", clean)
        self.assertNotIn("00:1A:2B:3C:4D:5E", clean)

    def test_jwt_and_reversible_vault(self):
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4ifQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        text = f"Yetki tokenı: {jwt} ve mail: ali@kurum.com"
        clean, reds, vault = self.sanitizer.sanitize_with_vault(text)
        self.assertIn("[MASKE_JWT_TOKEN]", clean)
        self.assertNotIn(jwt, clean)
        restored = self.sanitizer.desanitize(clean, vault)
        self.assertEqual(restored, text)


if __name__ == "__main__":
    unittest.main()
