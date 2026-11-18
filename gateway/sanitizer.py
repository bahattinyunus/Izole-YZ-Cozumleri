"""
Kurumsal DLP & PII Sanitizer (Data Loss Prevention Engine)
Kullanıcı istemlerindeki (prompts) hassas verileri (TCKN, Vergi Kimlik No, Kredi Kartı, IBAN, E-posta,
Telefon, İç Ağ IPv4, MAC Adresi ve Gizli Anahtarlar/JWT/PEM) yerel modele veya dışarıya gitmeden önce
tespit eder, maskeler ve istenirse yanıt aşamasında geri çözmek (reversible vault) üzere bellekte eşleştirir.
"""

import re
from typing import Dict, List, Tuple


class PIISanitizer:
    def __init__(self, mask_char: str = "*"):
        self.mask_char = mask_char

        # Regex kalıpları
        self.email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
        self.phone_regex = re.compile(r'(?:\+?90|0)?\s*[5]\d{2}[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}\b')
        self.iban_regex = re.compile(r'\bTR\d{2}(?:\s*\d{4}){5}\s*\d{2}\b', re.IGNORECASE)
        self.api_key_regex = re.compile(
            r'(?:sk-[a-zA-Z0-9_-]{20,64}|AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{36}|glpat-[a-zA-Z0-9_-]{20}|xox[baprs]-[a-zA-Z0-9-]{10,48})'
        )
        self.jwt_regex = re.compile(r'\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b')
        self.pem_key_regex = re.compile(
            r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----[\s\S]+?-----END (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'
        )
        self.internal_ip_regex = re.compile(
            r'\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})\b'
        )
        self.mac_regex = re.compile(r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b')
        self.potential_tckn_regex = re.compile(r'\b[1-9]\d{10}\b')
        self.potential_cc_regex = re.compile(r'\b(?:\d{4}[ -]?){3}\d{4}\b')

    @staticmethod
    def is_valid_tckn(number_str: str) -> bool:
        """TC Kimlik Numarası Doğrulama Algoritması (10. ve 11. hane modüler aritmetik kontrolü)"""
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
    def is_valid_vkn(number_str: str) -> bool:
        """Türkiye 10 Haneli Vergi Kimlik Numarası (VKN) Doğrulama Algoritması"""
        if len(number_str) != 10 or not number_str.isdigit():
            return False
        digits = [int(d) for d in number_str]
        total = 0
        for i in range(9):
            tmp = (digits[i] + (9 - i)) % 10
            if tmp == 0:
                total += 0
            else:
                total += (tmp * (2 ** (9 - i))) % 9
                if (tmp * (2 ** (9 - i))) % 9 == 0:
                    total += 9
        check_digit = (10 - (total % 10)) % 10
        return check_digit == digits[9]

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

    @staticmethod
    def is_valid_tr_iban(iban_str: str) -> bool:
        """ISO 7064 Mod 97-10 algoritması ile TR IBAN doğrulaması"""
        clean = re.sub(r'\s+', '', iban_str).upper()
        if len(clean) != 26 or not clean.startswith("TR"):
            return False
        # İlk 4 karakteri sona taşı, harfleri sayıya çevir (A=10 ... Z=35)
        rearranged = clean[4:] + clean[:4]
        numeric_str = ""
        for ch in rearranged:
            if ch.isdigit():
                numeric_str += ch
            elif ch.isalpha():
                numeric_str += str(ord(ch) - 55)
            else:
                return False
        return int(numeric_str) % 97 == 1

    def sanitize(self, text: str) -> Tuple[str, List[Dict[str, str]]]:
        """
        Metin içerisindeki tüm hassas bilgileri maskeler ve bulunan PII kaydını döndürür.
        """
        sanitized, redactions, _ = self.sanitize_with_vault(text)
        return sanitized, redactions

    def sanitize_with_vault(self, text: str) -> Tuple[str, List[Dict[str, str]], Dict[str, str]]:
        """
        Metin içerisindeki hassas bilgileri maskeler, PII kayıt listesini ve
        geri-çözülebilir (reversible tokenization) anahtar-değer kasasını (vault) döndürür.
        """
        redactions: List[Dict[str, str]] = []
        vault: Dict[str, str] = {}
        sanitized = text

        # 0. Özel Anahtar Blokları (PEM Private Keys)
        for match in self.pem_key_regex.finditer(sanitized):
            val = match.group()
            token = "[MASKE_ÖZEL_ANAHTAR]"
            sanitized = sanitized.replace(val, token)
            vault[token] = val
            redactions.append({"type": "PRIVATE_KEY", "matched": "-----BEGIN PRIVATE KEY-----..."})

        # 1. API Anahtarları / Secret Tokens
        for match in self.api_key_regex.finditer(sanitized):
            val = match.group()
            token = "[MASKE_GİZLİ_ANAHTAR]"
            sanitized = sanitized.replace(val, token)
            vault[token] = val
            redactions.append({"type": "API_KEY", "matched": val[:6] + "..."})

        # 1.b JWT Tokenlar
        for match in self.jwt_regex.finditer(sanitized):
            val = match.group()
            token = "[MASKE_JWT_TOKEN]"
            sanitized = sanitized.replace(val, token)
            vault[token] = val
            redactions.append({"type": "JWT_TOKEN", "matched": val[:12] + "..."})

        # 2. IBAN
        for match in self.iban_regex.finditer(sanitized):
            val = match.group()
            clean_iban = val.replace(" ", "")
            token = "[MASKE_IBAN]"
            sanitized = sanitized.replace(val, token)
            vault[token] = val
            redactions.append({
                "type": "IBAN",
                "matched": clean_iban[:4] + "..." + clean_iban[-2:],
                "mod97_valid": str(self.is_valid_tr_iban(clean_iban))
            })

        # 3. Kredi Kartı
        for match in self.potential_cc_regex.finditer(sanitized):
            val = match.group()
            if self.is_valid_luhn_credit_card(val):
                token = "[MASKE_KREDİ_KARTI]"
                sanitized = sanitized.replace(val, token)
                vault[token] = val
                redactions.append({"type": "CREDIT_CARD", "matched": "XXXX-XXXX-XXXX-" + val[-4:]})

        # 4. TC Kimlik Numarası
        for match in self.potential_tckn_regex.finditer(sanitized):
            val = match.group()
            if self.is_valid_tckn(val):
                token = "[MASKE_TCKN]"
                sanitized = sanitized.replace(val, token)
                vault[token] = val
                redactions.append({"type": "TCKN", "matched": val[:3] + "*****" + val[-2:]})

        # 5. E-posta Adresi
        for match in self.email_regex.finditer(sanitized):
            val = match.group()
            parts = val.split("@")
            user = parts[0][0] + "***" if len(parts[0]) > 0 else "***"
            token = f"[MASKE_EMAIL:{user}@{parts[1]}]"
            sanitized = sanitized.replace(val, token)
            vault[token] = val
            redactions.append({"type": "EMAIL", "matched": val})

        # 6. Telefon Numarası
        for match in self.phone_regex.finditer(sanitized):
            val = match.group()
            token = "[MASKE_TELEFON]"
            sanitized = sanitized.replace(val, token)
            vault[token] = val
            redactions.append({"type": "PHONE", "matched": val})

        # 7. İç Ağ (RFC1918) IPv4 Adresleri
        for match in self.internal_ip_regex.finditer(sanitized):
            val = match.group()
            token = "[MASKE_İÇ_İP]"
            sanitized = sanitized.replace(val, token)
            vault[token] = val
            redactions.append({"type": "INTERNAL_IP", "matched": val})

        # 8. MAC Adresleri
        for match in self.mac_regex.finditer(sanitized):
            val = match.group()
            token = "[MASKE_MAC_ADRESİ]"
            sanitized = sanitized.replace(val, token)
            vault[token] = val
            redactions.append({"type": "MAC_ADDRESS", "matched": val})

        return sanitized, redactions, vault

    @staticmethod
    def desanitize(text: str, vault: Dict[str, str]) -> str:
        """Maskelenmiş metindeki yer tutucuları (tokens) kasa (vault) yardımıyla orijinal haline döndürür."""
        restored = text
        for token, original in vault.items():
            restored = restored.replace(token, original)
        return restored

