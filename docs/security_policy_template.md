# 📋 Kurumsal Yapay Zeka Güvenlik Politikası Şablonu

Bu doküman, kurum içi Bilgi Güvenliği / CISO departmanlarının yürürlüğe koyabileceği örnek kurumsal yapay zeka kullanım ve veri gizliliği yönergesidir.

---

## 1. Amaç ve Kapsam
Bu politikanın amacı; kurum çalışanlarının yapay zeka teknolojilerinden faydalanırken kurumun ticari sırlarının, müşteri kişisel verilerinin (KVKK/GDPR) ve fikri mülkiyet haklarının korunmasını teminat altına almaktır.

---

## 2. Temel İlkeler ve Yasaklar

1. **Kamusal Bulut API Yasağı:**  
   Kurum içi kaynak kodlar, müşteri veritabanı dökümleri, finansal tablolar ve strateji belgeleri; OpenAI, Anthropic, Google Cloud gibi üçüncü taraf kamusal bulut yapay zeka servislerine yüklenemez veya istem (prompt) olarak girilemez.

2. **Gölge YZ (Shadow AI) Önleme:**  
   Çalışanların kurumsal işleri için kişisel mobil cihaz veya harici ağlar üzerinden yetkisiz yapay zeka araçlarını kullanması disiplin ve güvenlik ihlali kapsamındadır.

3. **Onaylı Kurumsal Ağ Geçidi Zorunluluğu:**  
   Tüm yapay zeka istemleri yalnızca kurum içi ağda (Intranet) çalışan, DLP filtreli ve denetim logu tutan **Sovereign AI Gateway** üzerinden yürütülecektir.

---

## 3. Veri Sınıflandırma ve Erişim Seviyeleri

| Veri Sınıfı | İzin Verilen Sistem | Açıklama |
| :--- | :--- | :--- |
| **Açık / Kamusal (Public)** | Dahili Gateway veya Onaylı WebUI | Basın bültenleri, genel yazım denetimi. |
| **İç Kullanım (Internal)** | Dahili İzole RAG (Genel Yetki) | Şirket içi yönetmelikler, genel prosedürler. |
| **Gizli / Hassas (Confidential)** | Dahili İzole RAG (Yüksek Yetki) | Finansal raporlar, müşteri analizleri, kaynak kodları. |
| **Çok Gizli / Stratejik (Secret)** | Yalnızca Hava Boşluklu (Air-Gapped) NPU/Sunucu | Ar-Ge tescilleri, savunma/kritik altyapı algoritmaları. |

---

## 4. Denetim ve İzlenebilirlik

- Ağ geçidinden geçen tüm sorguların içeriği kriptografik özet (SHA-256) olarak saklanır.
- DLP filtresi tarafından engellenen veya maskelenen kayıtlar periyodik olarak Güvenlik Operasyon Merkezi (SOC) tarafından incelenir.
