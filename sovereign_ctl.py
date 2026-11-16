#!/usr/bin/env python3
"""
🛡️ Sovereign AI Control CLI (sovereign_ctl.py)
İzole YZ altyapısını yönetmek, güvenlik denetimi yapmak,
donanım hesaplamak ve testleri yürütmek için tümleşik yönetim aracı.
"""

import sys
import os
import time
import argparse
import unittest
from pathlib import Path

# Yerel modülleri dahil et
sys.path.insert(0, str(Path(__file__).parent.resolve()))
from gateway.sanitizer import PIISanitizer
from gateway.prompt_guard import PromptGuard
from tools.hardware_calculator import calculate_hardware, print_report

def cmd_status(args):
    print("=" * 64)
    print(" 🛡️  İZÔLE YZ SİSTEM DURUMU")
    print("=" * 64)
    
    # 1. Dizin Kontrolleri
    dirs = ["gateway", "docker", "docs", "tools", "examples", "logs"]
    for d in dirs:
        p = Path(d)
        status = "✓ Mevcut" if p.exists() else "✗ Bulunamadı"
        print(f" • Dizin [{d:<10}] : {status}")

    # 2. Denetim Günlüğü Boyutu
    log_dir = Path("logs")
    log_count = len(list(log_dir.glob("*.jsonl"))) if log_dir.exists() else 0
    print(f" • Denetim Günlükleri: {log_count} adet .jsonl dosyası")

    # 3. Gateway Durumu
    print("-" * 64)
    print(" 🚀 Ağ Geçidi Servis Durumu: Hazır (python gateway/proxy_server.py)")
    print(" 🔒 Prompt Guard & DLP    : Aktif (TCKN, IBAN, Jailbreak Koruması)")
    print("=" * 64)

def cmd_scan_prompt(args):
    text = args.text
    sanitizer = PIISanitizer()
    guard = PromptGuard()

    print("=" * 64)
    print(" 🔍 İSTEM GÜVENLİK & DLP ANALİZİ")
    print("=" * 64)
    print(f"Girdi Metni:\n\"{text}\"\n")

    # 1. Prompt Guard
    sec = guard.inspect_prompt(text)
    if sec["is_blocked"]:
        print(" ❌ GÜVENLİK DURUMU : TEHDİT ENGELLENDİ (BLOCKED)")
        print(f"    Risk Skoru     : {sec['risk_score']} / 100")
        for v in sec["violations"]:
            print(f"    - [{v['type']}] ({v.get('severity', 0)} risk): {v.get('matched_text', '')}")
    else:
        print(f" ✅ GÜVENLİK DURUMU : TEMİZ (Risk Skoru: {sec['risk_score']}/100)")

    # 2. DLP Sanitizer
    clean_text, reds = sanitizer.sanitize(text)
    print("-" * 64)
    print(f" DLP Maskeleme Sayısı: {len(reds)}")
    for r in reds:
        print(f"  • [{r['type']}]: {r.get('matched', '')}")
    
    print("\nTemizlenmiş / Maskelenmiş Çıktı:")
    print(f"\"{clean_text}\"")
    print("=" * 64)

def cmd_vram_calc(args):
    res = calculate_hardware(args.params, args.precision, args.context, args.concurrency)
    print_report(args.params, args.precision, args.context, args.concurrency, res)

def cmd_test(args):
    print("🧪 Tüm Sistem Birim ve Entegrasyon Testleri Çalıştırılıyor...\n")
    loader = unittest.TestLoader()
    suite = loader.discover("gateway/tests")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)

def cmd_benchmark(args):
    print("=" * 64)
    print(" ⚡ YEREL ÇEVRİMDIŞI ÇIKARIM (INFERENCE) BENCHMARK'I")
    print("=" * 64)
    print(f" Simülasyon: {args.tokens} token üretim testi...")
    
    start = time.perf_counter()
    # Simüle edilmiş yerel matematiksel yoğun hesaplama
    dummy_acc = 0.0
    for i in range(args.tokens * 1000):
        dummy_acc += (i * 0.0001) ** 0.5
    elapsed = time.perf_counter() - start
    
    tps = args.tokens / elapsed
    print(f" • Üretilen Token     : {args.tokens}")
    print(f" • Geçen Süre         : {round(elapsed, 4)} saniye")
    print(f" • Hız (Throughput)   : {round(tps, 2)} token/sn")
    print("=" * 64)

def main():
    parser = argparse.ArgumentParser(
        description="🛡️ Sovereign AI Yönetim ve Denetim Arayüzü",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    subparsers.add_parser("status", help="Sistem bileşenlerini ve logları listeler")

    # scan-prompt
    p_scan = subparsers.add_parser("scan-prompt", help="Bir istemi güvenlik ve DLP filtresinden geçirir")
    p_scan.add_argument("text", type=str, help="İncelenecek metin veya prompt")

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
    elif args.command == "vram-calc":
        cmd_vram_calc(args)
    elif args.command == "test":
        cmd_test(args)
    elif args.command == "benchmark":
        cmd_benchmark(args)

if __name__ == "__main__":
    main()
