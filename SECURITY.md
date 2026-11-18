# 🛡️ Güvenlik Politikası (Security Policy)

Bu depo, ulusal ve kurumsal düzeyde **Hava Boşluklu (Air-Gapped) ve Egemen (Sovereign) Yapay Zeka** sistemleri için bir referans mimarisidir. Güvenlik ilkelerimiz Sıfır Güven (Zero-Trust) yaklaşımına dayanır.

---

## 🔒 Desteklenen Sürümler

| Sürüm | Destek Durumu | Güvenlik Güncellemeleri |
| :--- | :--- | :--- |
| `1.0.x` | ✅ Aktif Destek | Kritik güvenlik yamaları |
| `< 1.0` | ❌ Desteklenmiyor | Sürüm güncellemesi önerilir |

---

## 🚨 Güvenlik Açığı Bildirimi

Bir güvenlik açığı, DLP bypass veya Prompt Injection zaafı tespit ederseniz, lütfen bunu genel açık GitHub Issue'larında **paylaşmayınız**.

1. **Özel Bildirim:** Sorunu doğrudan repo yöneticilerine veya güvenlik sorumlusuna iletiniz.
2. **Sağlanması Gereken Detaylar:**
   - Açığın türü (Prompt Injection Bypass, PII Regex Kaçağı, Bellek Taşması vb.)
   - Yeniden oluşturma (PoC) adımları
   - Potansiyel etki analizi ve varsa önerilen yama
3. **Müdahale Süresi:** Güvenlik bildirimleri en geç **48 saat** içinde değerlendirilir ve doğrulanması durumunda acil güvenlik yaması yayınlanır.

---

## 🛡️ Güvenlik Taahhütleri

- **Sıfır Dış Ağ Çağrısı:** Gateway ve bağlı tüm alt bileşenler yerel ağ haricinde hiçbir harici telemetri, bulut analitiği veya otomatik güncelleme servisi barındırmaz.
- **Değiştirilemez Denetim Günlüğü:** Tüm istemler SHA-256 zincirli yerel denetim kütüklerinde (JSONL) tutulur.
- **DLP Sanitizasyonu:** TCKN, kredi kartı, IBAN ve API anahtarları gibi kritik PII verileri yerel çıkarım sunucusuna ulaşmadan filtrelenir.
