# ⚡ Uçta Bilişim (Edge AI) ve Donanım Egemenliği

> "Veri gizliliği, ancak verinin üretildiği donanım üzerindeki mutlak egemenlikle teminat altına alınabilir."  
> — *Team AYAZ / Arat Vizyonu & KAM (Otonom Sistemler) Saha Tecrübeleri*

---

## 1. Neden Edge AI ve Donanım Egemenliği?

Veriyi işlemek için merkezi bir buluta veya dış sunuculara göndermek iki büyük zaaf doğurur:
1. **İletişim Hattı Zaafı:** Radyo frekans karıştırması (Jamming), fiziksel kablo kesilmesi, siber dinleme.
2. **Gecikme (Latency):** Otonom araçlar, insansız hava/kara araçları (İHA/İKA) veya fabrika robotlarında milisaniyeler hayati önem taşır.

Çözüm, modelin doğrudan uç birimdeki NPU (Sinirsel İşlem Birimi) veya gömülü GPU üzerinde koşturulmasıdır.

---

## 2. Donanım Seviyeleri ve Seçim Matrisi

| Donanım Sınıfı | Örnek Platformlar | Güç Tüketimi (TDP) | Uygun Model Büyüklüğü | Kullanım Senaryosu |
| :--- | :--- | :--- | :--- | :--- |
| **Mikro Uç (Micro Edge)** | Hailo-8, Google Coral Edge TPU, Intel Movidius | 2W - 10W | CNN / Vision Modelleri (YOLO), Küçük Damıtılmış Modeller | Sensör füzyonu, kamera ucu anomali tespiti |
| **Mobil / Taktik Uç (Tactical Edge)** | NVIDIA Jetson Orin Nano / Orin NX (20W - 40W) | 15W - 50W | 1B - 3B LLM / SLM (Kuantize) | Otonom kara araçları, taktik saha asistanı |
| **Gömülü Ağır Uç (Heavy Edge)** | NVIDIA Jetson AGX Orin 64GB, Intel Xeon + Arc | 60W - 100W | 7B - 14B LLM (AWQ / INT4) | Komuta kontrol merkezi, saha analiz istasyonu |
| **Kurumsal On-Premise Sunucu** | 2x-4x NVIDIA RTX 4090 / L40S / H100 | 800W - 2500W | 70B+ LLM (FP16 veya AWQ) | Şirket içi tüm personelin kullandığı izole intranet YZ |

---

## 3. Kuantizasyon ve Damıtma (Distillation)

Edge üzerinde 70B bir modeli çalıştırmak güç kısıtları nedeniyle mümkün değildir. Bu sebeple iki temel teknik uygulanır:
1. **Bilgi Damıtma (Knowledge Distillation):** Büyük öğretmen modelin (Teacher) bilgi dağarcığı, 3B veya 7B boyutundaki küçük öğrenci modele (Student) aktarılır.
2. **Gelişmiş Kuantizasyon:**
   - **AWQ (Activation-aware Weight Quantization):** Kritik ağırlıkları 16-bit korurken geri kalanı 4-bit'e indirir; doğruluk kaybı %1'in altındadır.
   - **GGUF / llama.cpp:** GPU VRAM'i yetersiz kaldığında katmanları sistem RAM'ine ve CPU çekirdeklerine paylaştırarak donanım maliyetini minimize eder.
