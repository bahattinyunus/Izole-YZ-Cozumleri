#!/usr/bin/env python3
"""
İzole YZ Çevrimdışı Model Paketleyici (Air-Gapped Model Manifest & Verifier)
Hava boşluklu (Air-gapped) ortamlara güvenli transfer öncesi ve sonrasında
model ağırlıklarının (safetensors, bin, gguf, tokenizer json) SHA256 özetini çıkarır ve doğrular.
"""

import os
import sys
import json
import hashlib
import argparse
from pathlib import Path

def compute_sha256(file_path: Path, buffer_size: int = 65536) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(buffer_size):
            hasher.update(chunk)
    return hasher.hexdigest()

def generate_manifest(model_dir: Path, output_file: Path):
    if not model_dir.is_dir():
        print(f"Hata: '{model_dir}' geçerli bir dizin değil.")
        sys.exit(1)

    print(f"📦 Model dizini taranıyor: {model_dir}")
    manifest = {
        "version": "1.0",
        "model_dir": str(model_dir.resolve()),
        "files": []
    }

    total_size = 0
    file_count = 0

    for root, _, files in os.walk(model_dir):
        for file in files:
            # Gizli dosyaları ve önceki manifest dosyalarını atla
            if file.startswith(".") or file.endswith(".manifest.json"):
                continue
            
            p = Path(root) / file
            rel_path = p.relative_to(model_dir)
            size = p.stat().st_size
            total_size += size
            file_count += 1

            print(f" -> Özet hesaplanıyor: {rel_path} ({round(size / (1024**2), 2)} MB)")
            sha = compute_sha256(p)
            manifest["files"].append({
                "path": str(rel_path).replace("\\", "/"),
                "size_bytes": size,
                "sha256": sha
            })

    manifest["summary"] = {
        "total_files": file_count,
        "total_size_mb": round(total_size / (1024**2), 2),
        "total_size_gb": round(total_size / (1024**3), 3)
    }

    with open(output_file, "w", encoding="utf-8") as out:
        json.dump(manifest, out, indent=2, ensure_ascii=False)

    print(f"\n✅ Manifest başarıyla oluşturuldu: {output_file}")
    print(f"   Toplam Dosya: {file_count} | Toplam Boyut: {manifest['summary']['total_size_gb']} GB")

def verify_manifest(manifest_file: Path, target_dir: Path):
    if not manifest_file.is_file():
        print(f"Hata: Manifest dosyası bulunamadı: {manifest_file}")
        sys.exit(1)

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    files = manifest.get("files", [])
    print(f"🔍 Doğrulama Başlatılıyor: {len(files)} dosya denetlenecek...")
    
    passed = 0
    failed = []

    for item in files:
        rel_path = Path(item["path"])
        full_path = target_dir / rel_path
        expected_sha = item["sha256"]

        if not full_path.exists():
            print(f" ❌ EKSİK DOSYA: {rel_path}")
            failed.append((str(rel_path), "Eksik Dosya"))
            continue

        actual_sha = compute_sha256(full_path)
        if actual_sha.lower() == expected_sha.lower():
            print(f"  ✓ {rel_path} (Doğrulandı)")
            passed += 1
        else:
            print(f" ❌ BOZULMUŞ DOSYA (SHA Uyuşmazlığı): {rel_path}")
            failed.append((str(rel_path), "Hash Uyuşmuyor"))

    print("\n" + "=" * 50)
    if not failed:
        print(f"🎉 TÜM DOSYALAR BAŞARIYLA DOĞRULANDI ({passed}/{len(files)})")
        print("Model hava boşluklu (Air-gapped) sisteme yüklenmeye hazır.")
    else:
        print(f"⚠️ DOĞRULAMA HATASI: {len(failed)} dosyada problem tespit edildi!")
        for fn, reason in failed:
            print(f"  - {fn}: {reason}")
        sys.exit(2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Air-Gapped Model Doğrulama ve Manifest Oluşturucu")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", help="Dizin için SHA256 manifestosu üretir")
    create_parser.add_argument("model_dir", type=Path, help="Model dosyalarının bulunduğu dizin")
    create_parser.add_argument("--out", "-o", type=Path, default=Path("model_manifest.json"), help="Çıkış manifest JSON dosya yolu")

    verify_parser = subparsers.add_parser("verify", help="Mevcut manifestoya göre dizini doğrular")
    verify_parser.add_argument("manifest_file", type=Path, help="Daha önce üretilen manifest JSON dosyası")
    verify_parser.add_argument("target_dir", type=Path, help="Doğrulanacak hedef model dizini")

    args = parser.parse_args()

    if args.command == "create":
        generate_manifest(args.model_dir, args.out)
    elif args.command == "verify":
        verify_manifest(args.manifest_file, args.target_dir)
