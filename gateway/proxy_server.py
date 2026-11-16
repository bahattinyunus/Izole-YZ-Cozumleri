"""
Hafif ve İzole Kurumsal Yapay Zeka Ağ Geçidi (Sovereign AI Gateway)
Standard Library (Sıfır ek bağımlılık) ile çalışır.
OpenAI API uyumlu istekleri kabul eder:
- 🛡️ Prompt Guard: Jailbreak ve Enjeksiyon Saldırılarını engeller.
- 🔍 DLP Sanitizer: TCKN, Kredi Kartı, IBAN ve Gizli Anahtarları maskeler.
- 📜 Audit Logger: SHA-256 tabanlı değiştirilemez yerel denetim günlüğü tutar.
"""

import sys
import json
import time
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

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

class SovereignGatewayHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("X-Sovereign-Gateway", "Izole-YZ-v1.0")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health" or self.path == "/":
            self._set_headers(200)
            res = {
                "status": "healthy",
                "mode": "Air-Gapped Sovereign Gateway",
                "prompt_guard_active": True,
                "dlp_active": True,
                "audit_logging": True,
                "timestamp": time.time()
            }
            self.wfile.write(json.dumps(res, indent=2).encode("utf-8"))
        elif self.path == "/v1/models":
            self._set_headers(200)
            models = {
                "object": "list",
                "data": [
                    {"id": "llama3.1-8b-sovereign", "object": "model", "owned_by": "organization-local"},
                    {"id": "qwen2.5-coder-sovereign", "object": "model", "owned_by": "organization-local"}
                ]
            }
            self.wfile.write(json.dumps(models).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(b'{"error": "Not Found"}')

    def do_POST(self):
        if self.path == "/v1/chat/completions":
            start_time = time.time()
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
            user_id = self.headers.get("X-User-Id", "anonymous_corp_user")
            client_ip = self.client_address[0]

            raw_text_combined = " ".join([str(m.get("content", "")) for m in messages])

            # 1. Prompt Guard Güvenlik Denetimi (Jailbreak & Enjeksiyon Taraması)
            security_check = prompt_guard.inspect_prompt(raw_text_combined)
            if security_check["is_blocked"]:
                latency = (time.time() - start_time) * 1000.0
                audit_logger.log_transaction(
                    user_id=user_id,
                    client_ip=client_ip,
                    model=model,
                    raw_prompt=raw_text_combined,
                    sanitized_prompt="[ENGEL_GÜVENLİK_İHLALİ]",
                    redactions=[],
                    status="BLOCKED_SECURITY_VIOLATION",
                    latency_ms=latency
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

            # 2. DLP & Sanitization Aşama (PII Verilerini Maskele)
            total_redactions = []
            sanitized_messages = []

            for msg in messages:
                content = str(msg.get("content", ""))
                clean_content, reds = sanitizer.sanitize(content)
                if reds:
                    total_redactions.extend(reds)
                sanitized_messages.append({"role": msg.get("role"), "content": clean_content})

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
                        self._set_headers(200)
                        self.wfile.write(json.dumps(res_json).encode("utf-8"))
                        response_content = res_json.get("choices", [{}])[0].get("message", {}).get("content", "")
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
                        "items": total_redactions
                    }
                }
                self._set_headers(200)
                self.wfile.write(json.dumps(res_mock, ensure_ascii=False, indent=2).encode("utf-8"))

            latency = (time.time() - start_time) * 1000.0
            
            # 4. Güvenli Yerel Denetim Logu
            audit_logger.log_transaction(
                user_id=user_id,
                client_ip=client_ip,
                model=model,
                raw_prompt=raw_text_combined,
                sanitized_prompt=json.dumps(sanitized_messages, ensure_ascii=False),
                redactions=total_redactions,
                status="SUCCESS",
                latency_ms=latency
            )
        else:
            self._set_headers(404)
            self.wfile.write(b'{"error": "Endpoint not found"}')

def run_server(host="0.0.0.0", port=8080):
    server = HTTPServer((host, port), SovereignGatewayHandler)
    print("=" * 64)
    print(f" 🛡️  İzole YZ Kurumsal Ağ Geçidi Başlatıldı")
    print(f" 🌐 Dinleme Adresi : http://{host}:{port}")
    print(f" ⚔️  Prompt Guard   : AKTİF (Jailbreak & Enjeksiyon Kalkanı)")
    print(f" 🔒 DLP Sanitizer   : AKTİF (TCKN, CC, IBAN, API Key, Tel)")
    print(f" 📜 Denetim Günlüğü : logs/ dizinine JSONL olarak yazılıyor")
    print("=" * 64)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSunucu güvenle durduruldu.")
        server.server_close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port=port)
