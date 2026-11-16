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
        
        # Test amaçlı bilinen Luhn uyumlu TCKN algoritması çıktısı kontrolü
        # 10000000146 (1. hane 1, 2-9 0, 10. (7-0)%10=7 değil 4, kontrol)
        text_with_fake = "Müşteri no: 11111111111 kayıtlıdır."
        clean, reds = self.sanitizer.sanitize(text_with_fake)
        # Geçersiz olduğu için TCKN maskelenmemeli (false positive önleme)
        self.assertEqual(len([r for r in reds if r["type"] == "TCKN"]), 0)

if __name__ == "__main__":
    unittest.main()
