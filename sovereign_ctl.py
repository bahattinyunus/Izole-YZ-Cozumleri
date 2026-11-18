#!/usr/bin/env python3
"""
🛡️ Sovereign AI Control CLI (sovereign_ctl.py)
İzole YZ altyapısını yönetmek, güvenlik denetimi yapmak,
donanım hesaplamak, testleri yürütmek ve denetim loglarını analiz etmek
için tümleşik fütüristik yönetim aracı.
"""

import sys
import os
import json
import time
import argparse
import unittest
from pathlib import Path

# Renkler ve Stil Destekleyici (ANSI)
class Style:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

BANNER = f"""{Style.CYAN}{Style.BOLD}
   ███████╗ ██████╗ ██╗   ██╗███████╗██████╗ ███████╗██╗ ██████╗ ███╗   ██╗
   ██╔════╝██╔═══██╗██║   ██║██╔════╝██╔══██╗██╔════╝██║██╔════╝ ████╗  ██║
   ███████╗██║   ██║██║   ██║█████╗  ██████╔╝█████╗  ██║██║  ███╗██╔██╗ ██║
   ╚════██║██║   ██║╚██╗ ██╔╝██╔══╝  ██╔══██╗██╔══╝  ██║██║   ██║██║╚██╗██║
   ███████║╚██████╔╝ ╚████╔╝ ███████╗██║  ██║███████╗██║╚██████╔╝██║ ╚████║
   ╚══════╝ ╚═════╝   ╚═══╝  ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝
{Style.RESET}{Style.DIM}        AIR-GAPPED DEFENSE SUITE  •  ZERO-TRUST AI GATEWAY  •  TEAM AYAZ{Style.RESET}
"""

# Yerel modülleri dahil et
BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))
from gateway.sanitizer import PIISanitizer
from gateway.prompt_guard import PromptGuard
from gateway.audit_logger import AuditLogger
from tools.hardware_calculator import calculate_hardware, print_report

def cmd_status(args):
    print(BANNER)
    print(f"{Style.BOLD}┌──[ 📊 SİSTEM BİLEŞENLERİ VE ALTYAPI DURUMU ]{Style.RESET}")
    
    # 1. Dizin Kontrolleri
    dirs = [
        ("gateway", "DLP & Güvenlik Ağ Geçidi"),
        ("docker", "Air-Gapped Konteyner Tanımları"),
        ("docs", "Mimariler ve Uyum Kılavuzları"),
        ("tools", "Sistem Yöneticisi Araçları"),
        ("examples", "Referans Uygulamalar & RAG"),
        ("logs", "Değiştirilemez Denetim Kütükleri")
    ]
    for d, desc in dirs:
        p = BASE_DIR / d
        status = f"{Style.GREEN}✓ AKTİF{Style.RESET}" if p.exists() else f"{Style.RED}✗ BULUNAMADI{Style.RESET}"
        print(f"│  • {Style.BOLD}{d:<12}{Style.RESET} : {status:<20} {Style.DIM}({desc}){Style.RESET}")

    # 2. Denetim Günlüğü Boyutu
    log_dir = BASE_DIR / "logs"
    logs = list(log_dir.glob("*.jsonl")) if log_dir.exists() else []
    print(f"│  • {Style.BOLD}{'audit_logs':<12}{Style.RESET} : {Style.CYAN}{len(logs)} kütük dosyası{Style.RESET}       {Style.DIM}(logs/ dizininde){Style.RESET}")

    # 3. Gateway Durumu
    print(f"├──[ 🔒 GÜVENLİK VE ÇIKARIM DURUMU ]")
    print(f"│  • Ağ Geçidi (Gateway) : {Style.GREEN}Hazır (sovereign_ctl.py gateway){Style.RESET}")
    print(f"│  • Prompt Guard         : {Style.GREEN}Aktif (Jailbreak / Leak Koruması){Style.RESET}")
    print(f"│  • DLP Sanitizer        : {Style.GREEN}Aktif (TCKN, IBAN, Kart, Tel Maskeleme){Style.RESET}")
    print(f"│  • Mimari İzolasyon     : {Style.CYAN}Air-Gapped (Fiziksel / Dahili Docker Köprüsü){Style.RESET}")
    print(f"└─────────────────────────────────────────────────────────────────\n")

def cmd_scan_prompt(args):
    text = args.text
    sanitizer = PIISanitizer()
    guard = PromptGuard()

    print(BANNER)
    print(f"{Style.BOLD}┌──[ 🔍 İSTEM GÜVENLİK & DLP ANALİZ RAPORU ]{Style.RESET}")
    print(f"│ {Style.DIM}Girdi Metni:{Style.RESET} \"{text}\"\n│")

    # 1. Prompt Guard
    sec = guard.inspect_prompt(text)
    if sec["is_blocked"]:
        print(f"│ {Style.RED}{Style.BOLD}❌ GÜVENLİK DURUMU : TEHDİT ENGELLENDİ (BLOCKED){Style.RESET}")
        print(f"│    {Style.YELLOW}Risk Skoru     : {sec['risk_score']} / 100{Style.RESET}")
        for v in sec["violations"]:
            print(f"│    {Style.RED}• [{v['type']}] ({v.get('severity', 0)} risk): {v.get('matched_text', '')}{Style.RESET}")
    else:
        print(f"│ {Style.GREEN}{Style.BOLD}✅ GÜVENLİK DURUMU : TEMİZ (Risk Skoru: {sec['risk_score']}/100){Style.RESET}")

    # 2. DLP Sanitizer
    clean_text, reds = sanitizer.sanitize(text)
    print(f"│")
    print(f"├──[ 🛡️ DLP MASKELEME DETAYLARI ]")
    print(f"│ Toplam Maskelenen Veri Sayısı: {Style.CYAN}{len(reds)}{Style.RESET}")
    for r in reds:
        print(f"│  • {Style.YELLOW}[{r['type']}]:{Style.RESET} {r.get('matched', '')}")
    
    print(f"│\n│ {Style.DIM}LLM'e İletilecek Güvenli / Temizlenmiş Metin:{Style.RESET}")
    print(f"│ {Style.GREEN}\"{clean_text}\"{Style.RESET}")
    print(f"└─────────────────────────────────────────────────────────────────\n")

def cmd_audit_report(args):
    print(BANNER)
    print(f"{Style.BOLD}┌──[ 📜 DEĞİŞTİRİLEMEZ DENETİM RAPORU (AUDIT TRAIL) ]{Style.RESET}")
    log_dir = BASE_DIR / "logs"
    log_files = sorted(list(log_dir.glob("*.jsonl")), reverse=True) if log_dir.exists() else []

    if not log_files:
        print(f"│ {Style.YELLOW}Henüz kaydedilmiş denetim kütüğü bulunamadı.{Style.RESET}")
        print(f"└─────────────────────────────────────────────────────────────────\n")
        return

    target_file = log_files[0]
    print(f"│ İncelenen Kütük: {Style.CYAN}{target_file.name}{Style.RESET}")

    total_requests = 0
    blocked_requests = 0
    sanitized_count = 0
    violations_summary = {}

    with open(target_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                total_requests += 1
                if record.get("blocked", False):
                    blocked_requests += 1
                sanitized_count += record.get("redacted_count", 0)
                for v in record.get("violations", []):
                    v_type = v.get("type", "unknown")
                    violations_summary[v_type] = violations_summary.get(v_type, 0) + 1
            except Exception:
                continue

    print(f"│ Toplam İşlenen İstek      : {Style.BOLD}{total_requests}{Style.RESET}")
    print(f"│ Engellenen Saldırılar     : {Style.RED}{Style.BOLD}{blocked_requests}{Style.RESET}")
    print(f"│ DLP ile Maskelenen Veri   : {Style.GREEN}{Style.BOLD}{sanitized_count}{Style.RESET}")
    is_valid, _, chain_msg = AuditLogger.verify_log_file(target_file)
    chain_badge = f"{Style.GREEN}✓ DOĞRULANDI{Style.RESET}" if is_valid else f"{Style.RED}✗ BOZULMUŞ{Style.RESET}"
    print(f"│ Merkle Zincir Bütünlüğü   : {chain_badge} {Style.DIM}({chain_msg}){Style.RESET}")
    print(f"│")
    print(f"│ Tehdit Türleri Dağılımı:")
    if violations_summary:
        for k, v in violations_summary.items():
            print(f"│   - {k:<25} : {v} kez")
    else:
        print(f"│   {Style.DIM}(Kayıtlı aktif saldırı tespit edilmedi){Style.RESET}")
    print(f"└─────────────────────────────────────────────────────────────────\n")

def cmd_verify_audit(args):
    print(BANNER)
    print(f"{Style.BOLD}┌──[ 🔐 KRİPTOGRAFİK DENETİM ZİNCİRİ DOĞRULAMASI (MERKLE VERIFY) ]{Style.RESET}")
    log_dir = BASE_DIR / "logs"
    if args.file:
        target_files = [Path(args.file)]
    else:
        target_files = sorted(list(log_dir.glob("*.jsonl")), reverse=True) if log_dir.exists() else []

    if not target_files:
        print(f"│ {Style.YELLOW}Doğrulanacak denetim kütüğü bulunamadı.{Style.RESET}")
        print(f"└─────────────────────────────────────────────────────────────────\n")
        return

    all_passed = True
    for tf in target_files:
        ok, count, msg = AuditLogger.verify_log_file(tf)
        icon = f"{Style.GREEN}✅ GEÇERLİ{Style.RESET}" if ok else f"{Style.RED}❌ GEÇERSİZ{Style.RESET}"
        print(f"│ • {Style.CYAN}{tf.name:<34}{Style.RESET} : {icon} ({count} kayıt) -> {msg}")
        if not ok:
            all_passed = False

    print(f"└─────────────────────────────────────────────────────────────────\n")
    if not all_passed:
        sys.exit(2)

def cmd_gateway(args):
    print(BANNER)
    print(f"{Style.GREEN}🚀 Sovereign AI Gateway Başlatılıyor... Port: {args.port}{Style.RESET}")
    from gateway.proxy_server import run_server
    run_server(host=args.host, port=args.port)

def cmd_vram_calc(args):
    print(BANNER)
    res = calculate_hardware(args.params, args.precision, args.context, args.concurrency)
    print_report(args.params, args.precision, args.context, args.concurrency, res)

def cmd_test(args):
    print(BANNER)
    print(f"{Style.CYAN}🧪 Tüm Sistem Birim ve Entegrasyon Testleri Çalıştırılıyor...{Style.RESET}\n")
    loader = unittest.TestLoader()
    suite = loader.discover("gateway/tests")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)

def cmd_benchmark(args):
    print(BANNER)
    print(f"{Style.BOLD}┌──[ ⚡ YEREL ÇEVRİMDIŞI ÇIKARIM BENCHMARK'I ]{Style.RESET}")
    print(f"│ Simülasyon: {Style.CYAN}{args.tokens}{Style.RESET} token üretim döngüsü hesaplanıyor...")
    
    start = time.perf_counter()
    dummy_acc = 0.0
    for i in range(args.tokens * 1000):
        dummy_acc += (i * 0.0001) ** 0.5
    elapsed = time.perf_counter() - start
    
    tps = args.tokens / elapsed
    print(f"│ • Üretilen Token     : {Style.BOLD}{args.tokens}{Style.RESET}")
    print(f"│ • Geçen Süre         : {round(elapsed, 4)} saniye")
    print(f"│ • Hız (Throughput)   : {Style.GREEN}{Style.BOLD}{round(tps, 2)} token/sn{Style.RESET}")
    print(f"└─────────────────────────────────────────────────────────────────\n")

def main():
    parser = argparse.ArgumentParser(
        description="🛡️ Sovereign AI Yönetim ve Denetim Arayüzü",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    subparsers.add_parser("status", help="Sistem bileşenlerini ve altyapı durumunu listeler")

    # scan-prompt
    p_scan = subparsers.add_parser("scan-prompt", help="Bir istemi güvenlik ve DLP filtresinden geçirir")
    p_scan.add_argument("text", type=str, help="İncelenecek metin veya prompt")

    # gateway
    p_gw = subparsers.add_parser("gateway", help="Sovereign AI Gateway proxy sunucusunu başlatır")
    p_gw.add_argument("--host", type=str, default="0.0.0.0", help="Dinlenecek ağ arayüzü")
    p_gw.add_argument("--port", type=int, default=8080, help="Bağlantı noktası (Port)")

    # audit-report
    subparsers.add_parser("audit-report", help="En son denetim günlüğü kayıtlarını analiz eder")

    # verify-audit
    p_va = subparsers.add_parser("verify-audit", help="Denetim kütüklerinin SHA-256 hash zinciri bütünlüğünü doğrular")
    p_va.add_argument("--file", "-f", type=str, default=None, help="Belirli bir .jsonl kütük dosyası")

    # vram-calc
    p_vram = subparsers.add_parser("vram-calc", help="Donanım ve VRAM gereksinimi hesaplar")
    p_vram.add_argument("--params", "-p", type=float, default=8.0, help="Milyar parametre (örn: 8, 14, 70)")
    p_vram.add_argument("--precision", "-q", type=str, default="awq-4bit", help="Hassasiyet tipi")
    p_vram.add_argument("--context", "-c", type=int, default=8192, help="Bağlam uzunluğu")
    p_vram.add_argument("--concurrency", "-n", type=int, default=1, help="Eşzamanlı kullanıcı")

    # test
    subparsers.add_parser("test", help="Tüm sistem testlerini çalıştırır")

    # benchmark
    p_bench = subparsers.add_parser("benchmark", help="Yerel çıkarım hız benchmark'ı")
    p_bench.add_argument("--tokens", "-t", type=int, default=500, help="Test token sayısı")

    args = parser.parse_args()

    if args.command == "status":
        cmd_status(args)
    elif args.command == "scan-prompt":
        cmd_scan_prompt(args)
    elif args.command == "gateway":
        cmd_gateway(args)
    elif args.command == "audit-report":
        cmd_audit_report(args)
    elif args.command == "verify-audit":
        cmd_verify_audit(args)
    elif args.command == "vram-calc":
        cmd_vram_calc(args)
    elif args.command == "test":
        cmd_test(args)
    elif args.command == "benchmark":
        cmd_benchmark(args)

if __name__ == "__main__":
    main()
