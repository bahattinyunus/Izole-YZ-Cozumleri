# ⚖️ Küresel Regülasyonlar ve Kurumsal Uyumluluk Rehberi

Kurumsal şirketlerin yapay zekayı kamusal bulut servisleri üzerinden kullanırken karşılaştığı hukuki riskler ve İzole YZ mimarisinin sağladığı uyumluluk garantileri.

---

## 1. Karşılaştırmalı Regülasyon Tablosu

| Regülasyon / Standart | Coğrafya | Temel Kısıtlama | Kamusal Bulut Riski | İzole / Air-Gap Durumu |
| :--- | :--- | :--- | :--- | :--- |
| **KVKK (Kanun No: 6698)** | 🇹🇷 Türkiye | Kişisel verilerin açık rıza veya yeterlilik kararı olmadan yurt dışına aktarımı yasaktır (Madde 9). | Yüksek Ceza (Sunucuları yurt dışında olan API kullanımı ihlal doğurur). | **Tam Uyum** (Veri şirket yerel sunucusundan dışarı çıkmaz). |
| **GDPR** | 🇪🇺 Avrupa Birliği | Veri egemenliği, unutulma hakkı, üçüncü ülkelere veri transferi kısıtları (Schrems II kararı). | Ağır idari para cezaları (%4'e kadar küresel ciro). | **Tam Uyum** (Yerel işleme ve denetim günlüğü). |
| **EU AI Act (2024/2026)** | 🇪🇺 Avrupa Birliği | Yüksek riskli YZ sistemlerinde şeffaflık, denetlenebilirlik ve insan gözetimi zorunluluğu. | Kapalı kutu kamu API'lerinde model iç mantığı denetlenemez. | **Tam Denetlenebilirlik** (Açık kaynak model ağırlıkları & yerel loglar). |
| **DoD / NIST SP 800-53** | 🇺🇸 ABD Savunma | FedRAMP High, IL5/IL6 seviyeleri; internete fiziksel yalıtım zorunluluğu. | Kamusal API'ler askeri gizlilik dereceli verilerde kesinlikle yasaktır. | **Standart Gereksinimi** (Fiziksel hava boşluğu ve donanım kontrolü). |
| **PIPL** | 🇨🇳 Çin | Veri yerelleştirme (Data Localization) ve sınır ötesi güvenlik değerlendirmesi. | Onaysız veri çıkışı durdurma ve lisans iptali. | **Tam Uyum** (Sınır ötesi iletişim bulunmaz). |

---

## 2. Gölge YZ (Shadow AI) ve Hukuki Sorumluluk

Kurum çalışanlarının onaylanmamış kişisel hesaplarla kamuya açık sohbet botlarına (ChatGPT, Claude vb.) şirket belgelerini yüklemesi şu hukuki sonuçları doğurur:
1. **Ticari Sır İhlali:** Tescilli algoritmaların, müşteri portföylerinin ve finansal verilerin kamuya açık LLM modellerinin eğitim havuzuna karışma riski.
2. **Kişisel Veri İhlali:** Müşteri veya personel isim, telefon ve TCKN verilerinin üçüncü taraf sunucularda saklanması.
3. **Fikri Mülkiyet (IP) Riski:** Kod bloklarının genel modellere beslenmesi sonucu telif haklarının belirsizleşmesi.

**Kurumsal Çözüm:** Şirket içi yerel ağda çalışan, DLP filtreli ve kullanıcı dostu bir "Kurumsal Güvenli YZ Portalı" sunarak çalışanların gölge kanallara kaymasını %100 önlemek.
