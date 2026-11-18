"""
Kurumsal Güvenlik & Denetim Günlüğü (Immutable Cryptographic Audit Logger)
Model isteklerini, kimlik doğrulamalarını, güvenlik ihlallerini ve DLP müdahalelerini
SHA-256 hash zinciriyle (Merkle/Chain-of-Custody) birbirine bağlı, değiştirilemez yerel
JSON Lines formatında kayıt altına alır ve bütünlük doğrulaması (verify_chain) sunar.
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


GENESIS_HASH = "0" * 64


class AuditLogger:
    def __init__(self, log_dir: str = "logs", log_filename: Optional[str] = None):
        self.log_path = Path(log_dir)
        self.log_path.mkdir(parents=True, exist_ok=True)
        fname = log_filename or f"ai_gateway_audit_{time.strftime('%Y%m%d')}.jsonl"
        self.current_log_file = self.log_path / fname

    @staticmethod
    def hash_content(text: str) -> str:
        """İçerik parmak izi (Gizlilik için ham prompt yerine SHA-256 hash saklanır)"""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def compute_record_hash(record_without_hash: Dict[str, Any]) -> str:
        """Kaydın deterministik JSON serileştirmesi üzerinden SHA-256 zincir özeti üretir"""
        canonical = json.dumps(record_without_hash, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _get_last_hash(self) -> str:
        """Mevcut kütükteki son kaydın record_hash değerini döndürür (yoksa GENESIS_HASH)"""
        if not self.current_log_file.exists():
            return GENESIS_HASH
        last_line = ""
        try:
            with open(self.current_log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        last_line = line.strip()
            if last_line:
                data = json.loads(last_line)
                return data.get("record_hash", GENESIS_HASH)
        except Exception:
            return GENESIS_HASH
        return GENESIS_HASH

    def log_transaction(
        self,
        user_id: str,
        client_ip: str,
        model: str,
        raw_prompt: str,
        sanitized_prompt: str,
        redactions: List[Dict[str, str]],
        status: str = "SUCCESS",
        latency_ms: float = 0.0,
        violations: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        prev_hash = self._get_last_hash()
        blocked = status.startswith("BLOCKED")
        redacted_count = len(redactions)

        event: Dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "user_id": user_id,
            "client_ip": client_ip,
            "model_requested": model,
            "prompt_hash": self.hash_content(raw_prompt),
            "sanitized_hash": self.hash_content(sanitized_prompt),
            "dlp_triggered": redacted_count > 0,
            "redactions_count": redacted_count,
            "redacted_count": redacted_count,
            "redacted_types": [r["type"] for r in redactions],
            "blocked": blocked,
            "violations": violations or [],
            "status": status,
            "latency_ms": round(latency_ms, 2),
            "prev_hash": prev_hash,
        }

        event["record_hash"] = self.compute_record_hash(event)

        with open(self.current_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

        return event

    @classmethod
    def verify_log_file(cls, file_path: Path) -> Tuple[bool, int, str]:
        """
        Bir denetim kütüğü dosyasındaki kriptografik hash zincirini baştan sona doğrular.
        Dönüş: (is_valid, verified_records_count, message)
        """
        if not file_path.exists():
            return False, 0, f"Kütük dosyası bulunamadı: {file_path}"

        expected_prev_hash = GENESIS_HASH
        count = 0
        chained_count = 0

        with open(file_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    return False, count, f"Satır {line_no}: Geçersiz JSON formatı."

                count += 1
                # Geriye dönük uyumluluk: Eski kayıtlarda record_hash yoksa zincir başlangıcı kabul et
                if "record_hash" not in record or "prev_hash" not in record:
                    continue

                chained_count += 1
                actual_prev = record.get("prev_hash")
                if chained_count > 1 and actual_prev != expected_prev_hash:
                    return (
                        False,
                        count,
                        f"Satır {line_no}: Zincir kırılması tespit edildi! Beklenen prev_hash={expected_prev_hash[:12]}..., Bulunan={str(actual_prev)[:12]}..."
                    )

                stored_hash = record.pop("record_hash")
                recomputed = cls.compute_record_hash(record)
                if stored_hash != recomputed:
                    return (
                        False,
                        count,
                        f"Satır {line_no}: Kayıt bütünlüğü bozulmuş (Record Hash uyuşmazlığı)!"
                    )
                expected_prev_hash = stored_hash

        return True, count, f"Kütük doğrulandı ({count} toplam kayıt, {chained_count} kriptografik zincirli kayıt)."

