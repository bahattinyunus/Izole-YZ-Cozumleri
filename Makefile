.PHONY: help test status scan vram gateway benchmark clean docker-up docker-down

help:
	@echo "🛡️ Sovereign AI (İzole YZ) - Hızlı Komutlar:"
	@echo "  make status       - Sistem ve log bileşenlerinin durumunu gösterir"
	@echo "  make test         - Bütünleşik testleri (13 test) çalıştırır"
	@echo "  make gateway      - Yerel DLP ve Prompt Guard ağ geçidini başlatır"
	@echo "  make benchmark    - Yerel çıkarım performans testi çalıştırır"
	@echo "  make docker-up    - Air-gapped Docker yığınını ayağa kaldırır"
	@echo "  make docker-down  - Docker yığınını durdurur"
	@echo "  make clean        - Python önbellek ve geçici dosyaları temizler"

status:
	python sovereign_ctl.py status

test:
	python sovereign_ctl.py test

gateway:
	python sovereign_ctl.py gateway --port 8080

benchmark:
	python sovereign_ctl.py benchmark --tokens 1000

docker-up:
	docker compose -f docker/docker-compose.airgapped.yml up -d

docker-down:
	docker compose -f docker/docker-compose.airgapped.yml down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
