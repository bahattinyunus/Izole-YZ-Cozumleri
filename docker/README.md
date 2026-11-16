# 🐳 Hava Boşluklu (Air-Gapped) Docker Dağıtım Rehberi

Bu rehber, fiziksel olarak internet bağlantısı kesilmiş (Air-Gapped / Isolated) kurumsal veya savunma sunucularında İzole YZ yığınının nasıl ayağa kaldırılacağını anlatır.

---

## 1. Hazırlık Aşaması (İnternete Açık Güvenli Makinede)

Gerekli Docker imajları internet erişimi olan bir makinede çekilir ve `.tar` arşivleri olarak dışa aktarılır:

```bash
# 1. Gerekli imajları çekin
docker pull ollama/ollama:latest
docker pull qdrant/qdrant:latest
docker pull ghcr.io/open-webui/open-webui:main
docker build -t sovereign-gateway:latest -f docker/Dockerfile.gateway .

# 2. İmajları tek bir arşive sıkıştırın
docker save -o sovereign_ai_images.tar \
  ollama/ollama:latest \
  qdrant/qdrant:latest \
  ghcr.io/open-webui/open-webui:main \
  sovereign-gateway:latest
```

Model ağırlıklarını ve manifestosunu hazırlayın:
```bash
python tools/offline_model_packager.py create /path/to/llama-3.1-8b --out llama3_manifest.json
```

---

## 2. Transfer Aşaması (Veri Diyotu / Güvenli Medya)

`sovereign_ai_images.tar`, `docker-compose.airgapped.yml` ve model dosyaları onaylı fiziksel depolama birimi veya Veri Diyotu (Data Diode) üzerinden hedef izole sunucuya aktarılır.

---

## 3. İzole Sunucuda Kurulum (Sıfır İnternet)

```bash
# 1. İmajları yükleyin
docker load -i sovereign_ai_images.tar

# 2. Model bütünlüğünü doğrulayın
python tools/offline_model_packager.py verify llama3_manifest.json /path/to/target/models

# 3. .env dosyasını oluşturun
cp docker/.env.example docker/.env

# 4. Yığını başlatın
docker compose -f docker/docker-compose.airgapped.yml up -d
```

---

## 4. Ağ Mimarisi Güvencesi

`docker-compose.airgapped.yml` dosyasında:
- `sovereign-airgap-net` köprüsü `internal: true` olarak yapılandırılmıştır.
- Konteynerlerin varsayılan ağ geçidi (Default Gateway) kaldırılır, işletim sistemi seviyesinde bile paketlerin dış ağa yönlendirilmesi engellenir.
- Kullanıcılar sadece DLP filtresi ve Denetim Günlüğü içeren `sovereign-gateway` üzerinden modele erişebilir.
