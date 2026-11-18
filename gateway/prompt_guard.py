"""
Kurumsal İstem Güvenliği & Enjeksiyon Kalkanı (Prompt Guard & Jailbreak Defender)
Sistem yönergelerinin çalınmasını (System Prompt Leaks), Rol Gaspını (Jailbreak / DAN),
Dolaylı RAG Enjeksiyonlarını (Indirect Prompt Injection), Markdown/Görsel Veri Sızdırma (Exfiltration)
ve gizlenmiş (Base64/Hex/ROT13 vb.) saldırı girişimlerini tespit eder ve engeller.
"""

import re
import base64
import codecs
from typing import Tuple, List, Dict, Any


class PromptGuard:
    def __init__(self, risk_threshold: int = 50):
        self.risk_threshold = risk_threshold

        # Enjeksiyon ve Rol Gaspı (Jailbreak) Desenleri (İngilizce & Türkçe)
        self.jailbreak_patterns = [
            (r"(?i)\bignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|rules|directions)\b", 60, "SYS_PROMPT_OVERRIDE"),
            (r"(?i)\b(önceki|yukarıdaki)\s+(tüm\s+)?(talimatları|kuralları|yönergeleri)\s+(unut|yoksay|görmezden\s+gel)\b", 60, "TR_SYS_PROMPT_OVERRIDE"),
            (r"(?i)\byou\s+are\s+now\s+(DAN|unrestricted|in\s+developer\s+mode|freed|jailbroken)\b", 70, "JAILBREAK_PERSONA"),
            (r"(?i)\b(artık\s+kısıtlamasızsın|geliştirici\s+modundasın|hiçbir\s+kurala\s+tabi\s+değilsin)\b", 70, "TR_JAILBREAK_PERSONA"),
            (r"(?i)\b(repeat|print|output|display|show)\s+(the\s+)?(system\s+prompt|initial\s+instructions|secret\s+instructions)\b", 55, "SYSTEM_PROMPT_LEAK"),
            (r"(?i)\b(sistem\s+istemini|gizli\s+talimatları|başlangıç\s+komutlarını)\s+(yazdır|göster|ifşa\s+et|tekrarla)\b", 55, "TR_SYSTEM_PROMPT_LEAK"),
            (r"(?i)\bbypass\s+(all\s+)?(safety|security|content|ethical)\s+(filters|guidelines|protocols|guardrails)\b", 65, "SAFETY_BYPASS"),
            (r"(?i)\b(act\s+as|pretend\s+to\s+be|simulate)\s+an?\s+(unfiltered|unethical|malicious)\b", 55, "UNFILTERED_ROLEPLAY"),
            (r"(?i)\bdo\s+anything\s+now\b", 75, "DAN_ATTACK"),
            (r"(?i)\b(reveal|leak|dump)\s+(your\s+)?(hidden|internal|confidential)\s+(rules|guidelines|prompt|configuration)\b", 50, "PROMPT_EXTRACTION"),
            (r"(?i)(?:<\|im_start\|>system|\[INST\]\s*<<SYS>>|###\s*System\s*Instruction:)", 65, "CHATML_DELIMITER_INJECTION"),
        ]

        # Sistem / Komut & Kod Enjeksiyonu Desenleri
        self.command_injection_patterns = [
            (r"(?i)\b(rm\s+-rf|chmod\s+777|wget\s+http|curl\s+http|nc\s+-e|powershell\s+-enc|invoke-expression)\b", 80, "COMMAND_EXECUTION"),
            (r"(?i)(?:\/etc\/shadow|\/etc\/passwd|C:\\Windows\\System32|\.ssh\/id_rsa)", 75, "SYSTEM_FILE_PROBING"),
            (r"(?i)\b(?:DROP\s+TABLE|UNION\s+SELECT|xp_cmdshell|eval\s*\(\s*base64_decode)\b", 70, "CODE_SQL_INJECTION"),
        ]

        # Veri Sızdırma (Exfiltration) Desenleri (Markdown Image / Webhook Beacon)
        self.exfiltration_patterns = [
            (r"!\[[^\]]*\]\(https?:\/\/[^)]+\)", 65, "MARKDOWN_IMAGE_EXFILTRATION"),
            (r"(?i)\b(?:send|post|exfiltrate|forward)\s+(?:the\s+)?(?:conversation|data|context|keys)\s+to\s+https?:\/\/", 75, "EXTERNAL_WEBHOOK_EXFILTRATION"),
        ]

        # Base64 Aday Dizgisi Deseni (en az 20 karakterlik base64 blokları)
        self.base64_regex = re.compile(r'[A-Za-z0-9+/]{20,}={0,2}')
        # Hex Kodlanmış Dizgi Deseni (en az 24 hex karakter)
        self.hex_regex = re.compile(r'\b(?:0x)?([0-9a-fA-F]{24,})\b')

    def check_obfuscation(self, text: str) -> Tuple[int, List[Dict[str, Any]]]:
        """Gizlenmiş / Kodlanmış (Base64, Hex, ROT13 vb.) içerikleri denetler"""
        risk_score = 0
        detections = []
        all_check_patterns = self.jailbreak_patterns + self.command_injection_patterns

        # 1. Base64 Taraması
        matches = self.base64_regex.findall(text)
        for encoded in matches:
            padded = encoded + '=' * (-len(encoded) % 4)
            try:
                decoded_bytes = base64.b64decode(padded)
                decoded_text = decoded_bytes.decode('utf-8', errors='ignore')

                for pattern, score, label in all_check_patterns:
                    if re.search(pattern, decoded_text):
                        risk_score += score
                        detections.append({
                            "type": f"OBFUSCATED_B64_{label}",
                            "detail": f"Base64 içinde tespit edilen tehdit: '{label}'",
                            "severity": score
                        })
            except Exception:
                continue

        # 2. Hex Taraması
        hex_matches = self.hex_regex.findall(text)
        for hex_str in hex_matches:
            if len(hex_str) % 2 != 0:
                continue
            try:
                decoded_text = bytes.fromhex(hex_str).decode('utf-8', errors='ignore')
                for pattern, score, label in all_check_patterns:
                    if re.search(pattern, decoded_text):
                        risk_score += score
                        detections.append({
                            "type": f"OBFUSCATED_HEX_{label}",
                            "detail": f"Hex kodlaması içinde tespit edilen tehdit: '{label}'",
                            "severity": score
                        })
            except Exception:
                continue

        # 3. ROT13 Taraması (Eğer metin içinde açıkça rot13 referansı veya şüphesi varsa)
        if "rot13" in text.lower():
            try:
                rot_decoded = codecs.decode(text, 'rot_13')
                for pattern, score, label in all_check_patterns:
                    if re.search(pattern, rot_decoded):
                        risk_score += score
                        detections.append({
                            "type": f"OBFUSCATED_ROT13_{label}",
                            "detail": f"ROT13 içinde tespit edilen tehdit: '{label}'",
                            "severity": score
                        })
            except Exception:
                pass

        return risk_score, detections

    def inspect_prompt(self, text: str) -> Dict[str, Any]:
        """
        Gelen metni derinlemesine analiz eder, risk skoru ve ihlalleri döndürür.
        """
        total_risk = 0
        violations = []

        # 1. Açık Jailbreak & Enjeksiyon Taraması (EN + TR + ChatML)
        for pattern, score, label in self.jailbreak_patterns:
            match = re.search(pattern, text)
            if match:
                total_risk += score
                violations.append({
                    "type": label,
                    "matched_text": match.group(),
                    "severity": score
                })

        # 2. Komut & Kod Enjeksiyonu Taraması
        for pattern, score, label in self.command_injection_patterns:
            match = re.search(pattern, text)
            if match:
                total_risk += score
                violations.append({
                    "type": label,
                    "matched_text": match.group(),
                    "severity": score
                })

        # 3. Veri Sızdırma (Exfiltration) Taraması
        for pattern, score, label in self.exfiltration_patterns:
            match = re.search(pattern, text)
            if match:
                total_risk += score
                violations.append({
                    "type": label,
                    "matched_text": match.group(),
                    "severity": score
                })

        # 4. Gizlenmiş (Base64 / Hex / ROT13) Tehdit Taraması
        obf_risk, obf_detections = self.check_obfuscation(text)
        total_risk += obf_risk
        violations.extend(obf_detections)

        is_blocked = total_risk >= self.risk_threshold

        return {
            "is_safe": not is_blocked,
            "risk_score": min(100, total_risk),
            "is_blocked": is_blocked,
            "violations_count": len(violations),
            "violations": violations
        }

