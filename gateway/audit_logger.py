"""
Kurumsal Güvenlik & Denetim Günlüğü (Immutable Audit Logger)
Model isteklerini, kimlik doğrulamalarını ve DLP müdahalelerini yerel,
dışa kapalı JSON Lines formatında kayıt altına alır.
"""

import os
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List

class AuditLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_path = Path(log_dir)
        self.log_path.mkdir(parents=True, exist_ok=True)
        self.current_log_file = self.log_path / f"ai_gateway_audit_{time.strftime('%Y%m%d')}.jsonl"

    @staticmethod
    def hash_content(text: str) -> str:
        """İçerik parmak izi (Gizlilik için ham prompt yerine SHA-256 hash saklanır)"""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def log_transaction(
        self,
        user_id: str,
        client_ip: str,
        model: str,
        raw_prompt: str,
        sanitized_prompt: str,
        redactions: List[Dict[str, str]],
        status: str = "SUCCESS",
        latency_ms: float = 0.0
    ):
        event = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "user_id": user_id,
            "client_ip": client_ip,
            "model_requested": model,
            "prompt_hash": self.hash_content(raw_prompt),
            "sanitized_hash": self.hash_content(sanitized_prompt),
            "dlp_triggered": len(redactions) > 0,
            "redactions_count": len(redactions),
            "redacted_types": [r["type"] for r in redactions],
            "status": status,
            "latency_ms": round(latency_ms, 2)
        }

        with open(self.current_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

        return event
