"""
Kurumsal İstem Güvenliği & Enjeksiyon Kalkanı (Prompt Guard & Jailbreak Defender)
Sistem yönergelerinin çalınmasını (System Prompt Leaks), Rol Gaspını (Jailbreak / DAN)
ve gizlenmiş (Base64/Hex vb.) saldırı girişimlerini tespit eder ve engeller.
"""

import re
import base64
from typing import Tuple, List, Dict

class PromptGuard:
    def __init__(self, risk_threshold: int = 50):
        self.risk_threshold = risk_threshold
        
        # Enjeksiyon ve Rol Gaspı (Jailbreak) Desenleri
        self.jailbreak_patterns = [
            (r"(?i)\bignore\s+(all\s+)?(previous|above)\s+(instructions|prompts|rules)\b", 60, "SYS_PROMPT_OVERRIDE"),
            (r"(?i)\byou\s+are\s+now\s+(DAN|unrestricted|in\s+developer\s+mode|freed)\b", 70, "JAILBREAK_PERSONA"),
            (r"(?i)\b(repeat|print|output|display)\s+(the\s+)?(system\s+prompt|initial\s+instructions)\b", 50, "SYSTEM_PROMPT_LEAK"),
            (r"(?i)\bbypass\s+(all\s+)?(safety|security|content)\s+(filters|guidelines|protocols)\b", 65, "SAFETY_BYPASS"),
            (r"(?i)\b(act\s+as|pretend\s+to\s+be)\s+an?\s+unfiltered\b", 55, "UNFILTERED_ROLEPLAY"),
            (r"(?i)\bdo\s+anything\s+now\b", 75, "DAN_ATTACK"),
            (r"(?i)\b(reveal|leak)\s+(your\s+)?(hidden|internal)\s+(rules|guidelines)\b", 45, "PROMPT_EXTRACTION"),
        ]

        # Sistem / Komut Enjeksiyonu Desenleri
        self.command_injection_patterns = [
            (r"(?i)\b(rm\s+-rf|chmod\s+777|wget\s+http|curl\s+http|nc\s+-e|powershell\s+-enc)\b", 80, "COMMAND_EXECUTION"),
            (r"(?i)\b(\/etc\/shadow|\/etc\/passwd|C:\\Windows\\System32)\b", 75, "SYSTEM_FILE_PROBING"),
        ]

        # Base64 Aday Dizgisi Deseni (en az 24 karakterlik base64 blokları)
        self.base64_regex = re.compile(r'[A-Za-z0-9+/]{20,}={0,2}')

    def check_obfuscation(self, text: str) -> Tuple[int, List[Dict[str, str]]]:
        """Gizlenmiş / Kodlanmış (Base64 vb.) içerikleri denetler"""
        risk_score = 0
        detections = []

        matches = self.base64_regex.findall(text)
        for encoded in matches:
            # Padding tamamla
            padded = encoded + '=' * (-len(encoded) % 4)
            try:
                decoded_bytes = base64.b64decode(padded)
                decoded_text = decoded_bytes.decode('utf-8', errors='ignore')
                
                # Çözülen metinde tehdit ara
                for pattern, score, label in self.jailbreak_patterns:
                    if re.search(pattern, decoded_text):
                        risk_score += score
                        detections.append({
                            "type": f"OBFUSCATED_{label}",
                            "detail": f"Base64 içinde tespit edilen tehdit: '{pattern}'",
                            "severity": score
                        })
            except Exception:
                continue

        return risk_score, detections

    def inspect_prompt(self, text: str) -> Dict[str, any]:
        """
        Gelen metni derinlemesine analiz eder, risk skoru ve ihlalleri döndürür.
        """
        total_risk = 0
        violations = []

        # 1. Açık Jailbreak & Enjeksiyon Taraması
        for pattern, score, label in self.jailbreak_patterns:
            match = re.search(pattern, text)
            if match:
                total_risk += score
                violations.append({
                    "type": label,
                    "matched_text": match.group(),
                    "severity": score
                })

        # 2. Komut Enjeksiyonu Taraması
        for pattern, score, label in self.command_injection_patterns:
            match = re.search(pattern, text)
            if match:
                total_risk += score
                violations.append({
                    "type": label,
                    "matched_text": match.group(),
                    "severity": score
                })

        # 3. Gizlenmiş (Base64 vb.) Tehdit Taraması
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
