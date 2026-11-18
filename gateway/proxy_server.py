"""
Hafif ve İzole Kurumsal Yapay Zeka Ağ Geçidi (Sovereign AI Gateway)
Standard Library (Sıfır ek bağımlılık) ile çalışır.
OpenAI API uyumlu istekleri kabul eder:
- 🛡️ Prompt Guard: Jailbreak ve Enjeksiyon Saldırılarını engeller.
- 🔍 DLP Sanitizer: TCKN, Kredi Kartı, IBAN, IP, MAC, JWT ve Gizli Anahtarları maskeler (veya geri çözer).
- 📜 Audit Logger: SHA-256 hash zincirli değiştirilemez yerel denetim günlüğü tutar.
- 📊 Telemetry & Rate Limiter: /metrics ve /v1/audit/verify uç noktaları ile sıfır-güven izleme sağlar.
"""

import sys
import json
import time
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, List

# Yerel modülleri içe aktar
try:
    from gateway.sanitizer import PIISanitizer
    from gateway.audit_logger import AuditLogger
    from gateway.prompt_guard import PromptGuard
except ImportError:
    from sanitizer import PIISanitizer
    from audit_logger import AuditLogger
    from prompt_guard import PromptGuard

UPSTREAM_LLM_URL = "http://127.0.0.1:11434/v1/chat/completions"
UPSTREAM_ENABLED = False

sanitizer = PIISanitizer()
prompt_guard = PromptGuard(risk_threshold=50)
audit_logger = AuditLogger(log_dir="logs")


class GatewayTelemetry:
    def __init__(self, rate_limit_per_min: int = 120):
        self.start_time = time.time()
        self.total_requests = 0
        self.blocked_requests = 0
        self.dlp_redactions_total = 0
        self.rate_limited_requests = 0
        self.rate_limit_per_min = rate_limit_per_min
        self.client_windows: Dict[str, List[float]] = {}

    def check_rate_limit(self, client_key: str) -> bool:
        now = time.time()
        window = self.client_windows.get(client_key, [])
        window = [ts for ts in window if now - ts < 60.0]
        if len(window) >= self.rate_limit_per_min:
            self.client_windows[client_key] = window
            self.rate_limited_requests += 1
            return False
        window.append(now)
        self.client_windows[client_key] = window
        return True


telemetry = GatewayTelemetry(rate_limit_per_min=120)


class SovereignGatewayHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Standart çıktı kirliliğini önlemek için sessiz veya minimal log
        pass

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("X-Sovereign-Gateway", "Izole-YZ-v2.0")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health" or self.path == "/":
            self._set_headers(200)
            res = {
                "status": "healthy",
                "version": "2.0.0",
                "mode": "Air-Gapped Sovereign Gateway",
                "prompt_guard_active": True,
                "dlp_active": True,
                "audit_logging": True,
                "merkle_chain_active": True,
                "uptime_sec": round(time.time() - telemetry.start_time, 2),
                "timestamp": time.time()
            }
            self.wfile.write(json.dumps(res, indent=2).encode("utf-8"))
        elif self.path == "/metrics":
            self._set_headers(200)
            metrics = {
                "uptime_seconds": round(time.time() - telemetry.start_time, 2),
                "total_requests": telemetry.total_requests,
                "blocked_requests": telemetry.blocked_requests,
                "dlp_redactions_total": telemetry.dlp_redactions_total,
                "rate_limited_requests": telemetry.rate_limited_requests,
                "rate_limit_per_min": telemetry.rate_limit_per_min
            }
            self.wfile.write(json.dumps(metrics, indent=2).encode("utf-8"))
        elif self.path == "/v1/audit/verify":
            is_valid, count, msg = audit_logger.verify_log_file(audit_logger.current_log_file)
            self._set_headers(200 if is_valid else 409)
            res = {
                "verified": is_valid,
                "records_checked": count,
                "log_file": audit_logger.current_log_file.name,
                "message": msg
            }
            self.wfile.write(json.dumps(res, ensure_ascii=False, indent=2).encode("utf-8"))
        elif self.path == "/v1/models":
            self._set_headers(200)
            models = {
                "object": "list",
                "data": [
                    {"id": "llama3.1-8b-sovereign", "object": "model", "owned_by": "organization-local"},
                    {"id": "qwen2.5-coder-sovereign", "object": "model", "owned_by": "organization-local"},
                    {"id": "deepseek-r1-distill-32b-sovereign", "object": "model", "owned_by": "organization-local"}
                ]
            }
            self.wfile.write(json.dumps(models).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(b'{"error": "Not Found"}')

    def do_POST(self):
        if self.path == "/v1/chat/completions":
            start_time = time.time()
            telemetry.total_requests += 1

            user_id = self.headers.get("X-User-Id", "anonymous_corp_user")
            client_ip = self.client_address[0]

            # 0. Rate Limiting Kontrolü
            if not telemetry.check_rate_limit(f"{client_ip}:{user_id}"):
                self._set_headers(429)
                self.wfile.write(json.dumps({
                    "error": {
                        "message": "İstek sınırı aşıldı (Rate limit exceeded). Lütfen daha sonra tekrar deneyin.",
                        "type": "rate_limit_exceeded"
                    }
                }, ensure_ascii=False).encode("utf-8"))
                return

            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")

            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self._set_headers(400)
                self.wfile.write(b'{"error": "Invalid JSON body"}')
                return

            messages = payload.get("messages", [])
            model = payload.get("model", "llama3.1-8b-sovereign")
            reversible_dlp = self.headers.get("X-DLP-Reversible", "false").lower() == "true"

            raw_text_combined = " ".join([str(m.get("content", "")) for m in messages])

            # 1. Prompt Guard Güvenlik Denetimi (Jailbreak & Enjeksiyon Taraması)
            security_check = prompt_guard.inspect_prompt(raw_text_combined)
            if security_check["is_blocked"]:
                telemetry.blocked_requests += 1
                latency = (time.time() - start_time) * 1000.0
                audit_logger.log_transaction(
                    user_id=user_id,
                    client_ip=client_ip,
                    model=model,
                    raw_prompt=raw_text_combined,
                    sanitized_prompt="[ENGEL_GÜVENLİK_İHLALİ]",
                    redactions=[],
                    status="BLOCKED_SECURITY_VIOLATION",
                    latency_ms=latency,
                    violations=security_check["violations"]
                )
                self._set_headers(403)
                block_res = {
                    "error": {
                        "message": "İstem güvenlik politikası nedeniyle reddedildi (Prompt Injection / Jailbreak tespit edildi).",
                        "type": "security_policy_violation",
                        "risk_score": security_check["risk_score"],
                        "violations": security_check["violations"]
                    }
                }
                self.wfile.write(json.dumps(block_res, ensure_ascii=False, indent=2).encode("utf-8"))
                return

            # 2. DLP & Sanitization Aşaması (PII Verilerini Maskele + Kasa Oluştur)
            total_redactions = []
            combined_vault: Dict[str, str] = {}
            sanitized_messages = []

            for msg in messages:
                content = str(msg.get("content", ""))
                clean_content, reds, vault = sanitizer.sanitize_with_vault(content)
                if reds:
                    total_redactions.extend(reds)
                    combined_vault.update(vault)
                sanitized_messages.append({"role": msg.get("role"), "content": clean_content})

            telemetry.dlp_redactions_total += len(total_redactions)
            payload["messages"] = sanitized_messages

            # 3. Upstream Local LLM'e ilet veya Güvenli Çevrimdışı Simülatör çalıştır
            response_content = ""
            if UPSTREAM_ENABLED:
                try:
                    req = urllib.request.Request(
                        UPSTREAM_LLM_URL,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        res_json = json.loads(resp.read().decode("utf-8"))
                        response_content = res_json.get("choices", [{}])[0].get("message", {}).get("content", "")
                        if reversible_dlp and combined_vault:
                            response_content = sanitizer.desanitize(response_content, combined_vault)
                            res_json["choices"][0]["message"]["content"] = response_content
                        self._set_headers(200)
                        self.wfile.write(json.dumps(res_json).encode("utf-8"))
                except Exception as e:
                    self._set_headers(502)
                    err = {"error": f"Upstream LLM erişim hatası: {str(e)}"}
                    self.wfile.write(json.dumps(err).encode("utf-8"))
                    return
            else:
                response_content = (
                    "🛡️ [İzole YZ Ağ Geçidi]: İsteminiz güvenle işlendi. "
                    f"Güvenlik Skoru: Temiz (Risk: {security_check['risk_score']}/100). "
                    f"DLP Taraması: {len(total_redactions)} adet hassas veri maskelendi. "
                    "Veriniz yerel sınırların dışına çıkmadan işlenmektedir."
                )
                if reversible_dlp and combined_vault:
                    response_content = sanitizer.desanitize(response_content, combined_vault)

                res_mock = {
                    "id": f"chatcmpl-sovereign-{int(time.time())}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": model,
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response_content
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": len(raw_text_combined.split()),
                        "completion_tokens": len(response_content.split()),
                        "total_tokens": len(raw_text_combined.split()) + len(response_content.split())
                    },
                    "security_audit": {
                        "prompt_guard_passed": True,
                        "risk_score": security_check["risk_score"],
                        "dlp_redactions_applied": len(total_redactions),
                        "reversible_vault_active": reversible_dlp,
                        "items": total_redactions
                    }
                }
                self._set_headers(200)
                self.wfile.write(json.dumps(res_mock, ensure_ascii=False, indent=2).encode("utf-8"))

            latency = (time.time() - start_time) * 1000.0

            # 4. Güvenli Yerel Denetim Logu (Merkle Hash Zincirli)
            audit_logger.log_transaction(
                user_id=user_id,
                client_ip=client_ip,
                model=model,
                raw_prompt=raw_text_combined,
                sanitized_prompt=json.dumps(sanitized_messages, ensure_ascii=False),
                redactions=total_redactions,
                status="SUCCESS",
                latency_ms=latency,
                violations=[]
            )
        else:
            self._set_headers(404)
            self.wfile.write(b'{"error": "Endpoint not found"}')


def run_server(host="0.0.0.0", port=8080):
    server = HTTPServer((host, port), SovereignGatewayHandler)
    print("=" * 64)
    print(f" 🛡️  İzole YZ Kurumsal Ağ Geçidi v2.0 Başlatıldı")
    print(f" 🌐 Dinleme Adresi : http://{host}:{port}")
    print(f" ⚔️  Prompt Guard   : AKTİF (EN/TR Jailbreak, Hex/B64/ROT13, ChatML)")
    print(f" 🔒 DLP Sanitizer   : AKTİF (TCKN, CC, IBAN, IP, MAC, JWT, API Key)")
    print(f" 📜 Denetim Günlüğü : SHA-256 Hash Zincirli JSONL (logs/)")
    print("=" * 64)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSunucu güvenle durduruldu.")
        server.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port=port)

