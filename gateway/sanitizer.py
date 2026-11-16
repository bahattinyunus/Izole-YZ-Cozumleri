"""
Kurumsal DLP & PII Sanitizer (Data Loss Prevention Engine)
Kullanıcı istemlerindeki (prompts) hassas verileri (TCKN, Kredi Kartı, IBAN, E-posta,
Telefon ve Gizli Anahtarlar) yerel modele veya dışarıya gitmeden önce tespit ve maskeleme yapar.
"""

import re
from typing import Dict, List, Tuple

class PIISanitizer:
    def __init__(self, mask_char: str = "*"):
        self.mask_char = mask_char
        
        # Regex kalıpları
        self.email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
        self.phone_regex = re.compile(r'(?:\+?90|0)?\s*[5]\d{2}[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}')
        self.iban_regex = re.compile(r'\bTR\d{2}(?:\s*\d{4}){5}\s*\d{2}\b', re.IGNORECASE)
        self.api_key_regex = re.compile(r'(?:sk-[a-zA-Z0-9]{20,48}|AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{36})')
        self.potential_tckn_regex = re.compile(r'\b[1-9]\d{10}\b')
        self.potential_cc_regex = re.compile(r'\b(?:\d{4}[ -]?){3}\d{4}\b')

    @staticmethod
    def is_valid_tckn(number_str: str) -> bool:
        """TC Kimlik Numarası Doğrulama Algoritması"""
        if len(number_str) != 11 or not number_str.isdigit() or number_str[0] == '0':
            return False
        digits = [int(d) for d in number_str]
        
        # 1, 3, 5, 7 ve 9. hanelerin toplamı
        odd_sum = sum(digits[0:9:2])
        # 2, 4, 6 ve 8. hanelerin toplamı
        even_sum = sum(digits[1:8:2])
        
        # 10. hane kuralı
        digit_10 = ((odd_sum * 7) - even_sum) % 10
        if digit_10 != digits[9]:
            return False
            
        # 11. hane kuralı: ilk 10 hanenin toplamının mod 10'u
        digit_11 = sum(digits[:10]) % 10
        return digit_11 == digits[10]

    @staticmethod
    def is_valid_luhn_credit_card(card_str: str) -> bool:
        """Luhn algoritması ile kredi kartı kontrolü"""
        clean_num = re.sub(r'[\s-]', '', card_str)
        if not (13 <= len(clean_num) <= 19) or not clean_num.isdigit():
            return False
            
        digits = [int(c) for c in clean_num]
        checksum = 0
        reverse_digits = digits[::-1]
        
        for i, d in enumerate(reverse_digits):
            if i % 2 == 1:
                doubled = d * 2
                checksum += doubled - 9 if doubled > 9 else doubled
            else:
                checksum += d
        return checksum % 10 == 0

    def sanitize(self, text: str) -> Tuple[str, List[Dict[str, str]]]:
        """
        Metin içerisindeki tüm hassas bilgileri maskeler ve bulunan PII kaydını döndürür.
        """
        redactions = []
        sanitized = text

        # 1. API Anahtarları / Secret Tokens
        for match in self.api_key_regex.finditer(text):
            val = match.group()
            sanitized = sanitized.replace(val, "[MASKE_GİZLİ_ANAHTAR]")
            redactions.append({"type": "API_KEY", "matched": val[:6] + "..."})

        # 2. IBAN
        for match in self.iban_regex.finditer(text):
            val = match.group()
            clean_iban = val.replace(" ", "")
            sanitized = sanitized.replace(val, "[MASKE_IBAN]")
            redactions.append({"type": "IBAN", "matched": clean_iban[:4] + "..." + clean_iban[-2:]})

        # 3. Kredi Kartı
        for match in self.potential_cc_regex.finditer(text):
            val = match.group()
            if self.is_valid_luhn_credit_card(val):
                sanitized = sanitized.replace(val, "[MASKE_KREDİ_KARTI]")
                redactions.append({"type": "CREDIT_CARD", "matched": "XXXX-XXXX-XXXX-" + val[-4:]})

        # 4. TC Kimlik Numarası
        for match in self.potential_tckn_regex.finditer(text):
            val = match.group()
            if self.is_valid_tckn(val):
                sanitized = sanitized.replace(val, "[MASKE_TCKN]")
                redactions.append({"type": "TCKN", "matched": val[:3] + "*****" + val[-2:]})

        # 5. E-posta Adresi
        for match in self.email_regex.finditer(sanitized):
            val = match.group()
            parts = val.split("@")
            user = parts[0][0] + "***" if len(parts[0]) > 0 else "***"
            sanitized = sanitized.replace(val, f"[MASKE_EMAIL:{user}@{parts[1]}]")
            redactions.append({"type": "EMAIL", "matched": val})

        # 6. Telefon Numarası
        for match in self.phone_regex.finditer(sanitized):
            val = match.group()
            sanitized = sanitized.replace(val, "[MASKE_TELEFON]")
            redactions.append({"type": "PHONE", "matched": val})

        return sanitized, redactions
