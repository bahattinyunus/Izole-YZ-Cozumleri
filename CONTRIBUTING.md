# 🤝 Katkı Sağlama Kılavuzu (Contributing Guide)

**İzole YZ Çözümleri** projesine katkıda bulunmak istediğiniz için teşekkür ederiz! Bu proje; savunma sanayii, bankacılık ve yüksek güvenlik gerektiren kurumlar için referans mimari teşkil etmektedir.

---

## 📌 Temel İlkeler

1. **Sıfır Dış Bağımlılık (Zero-Dependency) Prensibi:**
   - Gateway çekirdeği ve CLI araçları mümkün olduğunca harici Python paketlerine (pip) bağımlı olmadan standart kütüphane ile çalışmalıdır.
   - Air-gapped (internetsiz) ortamlarda `pip install` imkanı bulunmadığı unutulmamalıdır.
2. **Kriptografik ve Deterministik Tasarım:**
   - Güvenlik ve denetim loglarında SHA-256 doğrulama zinciri bozulmamalıdır.
3. **Kapsamlı Test Kapsamı:**
   - Eklenen her yeni DLP filtresi veya Prompt Guard kuralı için `gateway/tests/` altına birim testi eklenmelidir.

---

## 🛠️ Yerel Geliştirme Adımları

### 1. Depoyu Klonlayın
```bash
git clone https://github.com/bahattinyunus/Izole-YZ-Cozumleri.git
cd Izole-YZ-Cozumleri
```

### 2. Testleri Çalıştırın
Tüm birim ve entegrasyon testlerinin geçtiğinden emin olun:
```bash
python sovereign_ctl.py test
```

### 3. Kod Standartları ve Formatlama
Kodlarınızı Python PEP 8 standartlarına uygun tutun:
```bash
python -m flake8 gateway tools sovereign_ctl.py
```

### 4. Pull Request Gönderimi
- PR başlığında yapılan değişikliği açıkça belirtin (örn: `feat(dlp): Pasaport numarası maskeleme kuralı eklendi`).
- İlgili testlerin çıktısını PR açıklamasında paylaşın.
