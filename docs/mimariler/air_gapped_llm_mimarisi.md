# 🛡️ Hava Boşluklu (Air-Gapped) LLM Dağıtım Mimarisi

Hava boşluklu mimari, bilişim sistemlerinin kamusal internetten ve harici güvenilmeyen ağlardan hem mantıksal hem de fiziksel olarak tamamen yalıtılması ilkesine dayanır.

---

## 1. Temel Tehdit Modeli ve Çözüm

| Risk Faktörü | Kamusal Bulut / API | Air-Gapped Savunma Çözümü |
| :--- | :--- | :--- |
| **Veri Sızıntısı (Exfiltration)** | Yüksek (Prompt ve bağlam dış sunuculara akar) | Sıfır (Dış ağ kablosu ve kablosuz donanım bulunmaz) |
| **Model Zehirlenmesi / Güvenlik Açığı** | Sürekli dış güncellemeler risk taşır | Statik, SHA256 ile doğrulanmış dondurulmuş ağırlıklar |
| **Hizmet Kesintisi / Ambargo** | Dış API kesintisi veya lisans iptali | %100 yerel donanım egemenliği |
| **Gölge YZ (Shadow AI)** | Çalışanlar gizli hesaplarla API kullanır | Kurum içine yüksek hızlı yerel model arayüzü sunulur |

---

## 2. Model Doğrulama ve Güvenli Tedarik Zinciri

Hava boşluklu sisteme aktarılacak model ağırlıkları şu adımlardan geçmelidir:

1. **Pickle / Güvensiz Format Yasağı:** `.pt` veya `.bin` yerine yalnızca güvenli `.safetensors` veya dondurulmuş `.gguf` formatları kabul edilir.
2. **Kriptografik Bütünlük (SHA-256):** `tools/offline_model_packager.py` kullanılarak üretim bandında kontrol özeti üretilir, aktarım sonrası doğrulanır.
3. **Statik Kod Analizi:** Model konfigürasyon dosyalarındaki (`config.json`, `tokenizer.json`) harici kod çalıştırma (`trust_remote_code=True`) bayrakları kapatılır.

---

## 3. Katmanlı İzolasyon Topolojisi

```
[ Güvenilir Kullanıcı Ağı (LAN) ]
              │
              ▼  (HTTP / Intranet)
   ┌──────────────────────┐
   │ Sovereign AI Gateway │  <-- DLP Filtresi (TCKN, IBAN Maskeleme)
   └──────────┬───────────┘
              │  (Yalnızca İzole Docker Bridge: internal=true)
              ▼
   ┌──────────────────────┐
   │ Local Inference Core │  <-- vLLM / Ollama (NVIDIA CUDA / NPU)
   └──────────────────────┘
              │
              ▼
    [ Model Ağırlıkları (Read-Only Volume) ]
```
