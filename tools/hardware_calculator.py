#!/usr/bin/env python3
"""
İzole YZ Donanım & Bellek Hesaplayıcı (Sovereign AI Hardware Calculator)
Kurumsal ve yerel (on-premise) LLM dağıtımları için gerekli VRAM, Sistem RAM'i
ve bant genişliği gereksinimlerini hesaplar.
"""

import sys
import argparse

MODEL_CONFIGS = {
    "1b": 1.1,
    "3b": 3.2,
    "7b": 7.24,
    "8b": 8.03,
    "13b": 13.0,
    "14b": 14.7,
    "32b": 32.5,
    "70b": 70.6,
    "qwen2.5-coder-7b": 7.6,
    "llama3.1-8b": 8.0,
    "llama3.3-70b": 70.6,
    "mistral-small-24b": 24.0,
}

PRECISION_MULTIPLIERS = {
    "fp16": 2.0,      # 2 byte per param
    "bf16": 2.0,
    "int8": 1.0,      # 1 byte per param
    "int4": 0.5,      # 0.5 byte per param
    "awq-4bit": 0.55, # ~4.4 bit with overhead
    "gguf-q4_k_m": 0.58,
    "gguf-q8_0": 1.08,
}

def calculate_hardware(param_billions: float, precision: str, context_len: int, concurrency: int = 1):
    bytes_per_param = PRECISION_MULTIPLIERS.get(precision.lower(), 2.0)
    
    # Model ağırlıkları bellek gereksinimi (GB)
    model_weight_gb = (param_billions * 1e9 * bytes_per_param) / (1024 ** 3)
    
    # KV Cache bellek hesabı: 2 * num_layers * hidden_size * num_heads * bytes * context_len
    # Yaklaşık pratik katsayı: context başına ~0.5MB - 1.2MB per 1k token (fp16)
    kv_cache_per_1k_gb = 0.0008 * (param_billions / 7.0) * bytes_per_param
    total_kv_cache_gb = (context_len / 1000.0) * kv_cache_per_1k_gb * concurrency
    
    # CUDA runtime & framework overhead (~%15 emniyet payı)
    cuda_overhead_gb = max(1.5, model_weight_gb * 0.12)
    
    total_vram_needed = model_weight_gb + total_kv_cache_gb + cuda_overhead_gb
    recommended_vram = round(total_vram_needed * 1.15, 1)
    
    # Donanım tavsiyesi
    recommendation = []
    if recommended_vram <= 8:
        recommendation.append("Giriş Düzeyi Edge: NVIDIA RTX 4060 Ti 16GB / Jetson Orin Nano (Kuantize)")
    elif recommended_vram <= 16:
        recommendation.append("Tek Kart Kurumsal İş İstasyonu: RTX 4080 (16GB) veya RTX 4000 Ada (20GB)")
    elif recommended_vram <= 24:
        recommendation.append("İş İstasyonu / Uç Sunucu: RTX 3090 / 4090 (24GB) veya NVIDIA A10G (24GB)")
    elif recommended_vram <= 48:
        recommendation.append("Sunucu Sınıfı: 2x RTX 4090 / 1x NVIDIA A6000 Ada (48GB) / 1x L40S")
    elif recommended_vram <= 80:
        recommendation.append("Veri Merkezi: 1x NVIDIA H100 NVL (80GB) veya 2x A6000")
    else:
        num_cards = int((recommended_vram // 80) + 1)
        recommendation.append(f"Küme Dağıtımı: {num_cards}x NVIDIA H100 / A100 (80GB) NVLink")

    return {
        "model_weight_gb": round(model_weight_gb, 2),
        "kv_cache_gb": round(total_kv_cache_gb, 2),
        "cuda_overhead_gb": round(cuda_overhead_gb, 2),
        "minimum_vram_gb": round(total_vram_needed, 2),
        "recommended_vram_gb": recommended_vram,
        "recommended_system_ram_gb": round(recommended_vram * 1.5, 0),
        "hardware_recommendation": recommendation[0]
    }

def print_report(params, precision, context, concurrency, res):
    print("=" * 64)
    print(" 🛡️  İZÔLE YZ DONANIM & VRAM KAPASİTE RAPORU")
    print("=" * 64)
    print(f" • Parametre Boyutu   : {params} Milyar (Billion)")
    print(f" • Hassasiyet         : {precision.upper()}")
    print(f" • Bağlam (Context)   : {context:,} token")
    print(f" • Eşzamanlı İstek    : {concurrency}")
    print("-" * 64)
    print(f" [1] Ham Model Ağırlığı       : {res['model_weight_gb']} GB")
    print(f" [2] KV Cache Tüketimi        : {res['kv_cache_gb']} GB")
    print(f" [3] CUDA / Framework Payı    : {res['cuda_overhead_gb']} GB")
    print("-" * 64)
    print(f" 🎯 Asgari Gerekli VRAM       : {res['minimum_vram_gb']} GB")
    print(f" 🚀 Önerilen Güvenli VRAM     : {res['recommended_vram_gb']} GB")
    print(f" 💾 Asgari Sistem RAM (Host)  : {res['recommended_system_ram_gb']} GB")
    print("-" * 64)
    print(f" 🖥️  Donanım Tavsiyesi        :\n    -> {res['hardware_recommendation']}")
    print("=" * 64)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="İzole YZ Donanım ve VRAM İhtiyaç Hesaplayıcısı")
    parser.add_argument("--params", "-p", type=str, default="8b", help="Model parametresi (örn: 7b, 8b, 70b veya özel sayı 14)")
    parser.add_argument("--precision", "-q", type=str, default="awq-4bit", choices=list(PRECISION_MULTIPLIERS.keys()), help="Kuantizasyon / Hassasiyet tipi")
    parser.add_argument("--context", "-c", type=int, default=8192, help="Hedef bağlam penceresi (token)")
    parser.add_argument("--concurrency", "-n", type=int, default=1, help="Eşzamanlı kullanıcı / istek sayısı")
    
    args = parser.parse_args()
    
    val = args.params.lower().strip()
    if val in MODEL_CONFIGS:
        param_val = MODEL_CONFIGS[val]
    else:
        try:
            param_val = float(val.replace("b", ""))
        except ValueError:
            print(f"Hata: Geçersiz parametre boyutu '{args.params}'. Örnekler: 7b, 8b, 70b, 14")
            sys.exit(1)
            
    results = calculate_hardware(param_val, args.precision, args.context, args.concurrency)
    print_report(param_val, args.precision, args.context, args.concurrency, results)
