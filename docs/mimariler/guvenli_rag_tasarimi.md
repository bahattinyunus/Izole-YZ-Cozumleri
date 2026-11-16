# 📚 Güvenli ve İzole RAG (Retrieval-Augmented Generation) Tasarımı

Kurumsal bilginin (ERP, CRM, sözleşmeler, Ar-Ge dokümanları) yapay zekaya aktarılmasında en kritik halka RAG mimarisidir. İzole bir sistemde RAG uygulanırken dikkat edilmesi gereken temel prensipler aşağıda özetlenmiştir.

---

## 1. Çevrimdışı Embedding (Vektörleştirme)

Kamuya açık embedding API'leri (OpenAI text-embedding-3 vb.) yerine tamamen çevrimdışı çalışan modeller tercih edilmelidir:
- **Tavsiye Edilen Modeller:** `BAAI/bge-m3`, `nomic-embed-text-v1.5`, `snowflake-arctic-embed`.
- **Avantajı:** Türkçe dil desteği, çok dilli (multilingual) arama, GPU veya CPU üzerinde sıfır internet bağımlılığıyla çalışma.

---

## 2. Rol Tabanlı Erişim Kontrolü (RBAC ile Vektör Filtreleme)

Klasik RAG sistemlerinde en büyük güvenlik açığı, alt seviye yetkili bir kullanıcının arama yaptığında üst yönetim maaş veya gizli finans tablolarını prompt bağlamına çekebilmesidir.

**İzole RAG Çözümü:**
Vektör veritabanına (Qdrant / Milvus) veri yazılırken metadata katmanına erişim izinleri eklenir:

```json
{
  "chunk_id": "doc_contract_981",
  "text": "2026 yılı savunma bütçesi tahsisi...",
  "metadata": {
    "clearance_level": "SECRET",
    "department": ["RND", "EXECUTIVE"],
    "allowed_roles": ["sysadmin", "director"]
  }
}
```

Kullanıcı arama yaptığında, kullanıcının kurum içi token'ından alınan roller vektör filtresi olarak sorguya zorunlu kılınır:

```python
search_filter = {
    "must": [
        {"key": "clearance_level", "match": {"value": user_clearance}},
        {"key": "department", "match": {"value": user_department}}
    ]
}
```

---

## 3. Hibrit Arama (Dense Vector + BM25 Sparse Search)

Sadece kosinüs benzerliğine dayalı semantik arama, teknik terimler, kod numaraları veya seri no'larda hata yapabilir. İzole kurumsal yapılarda:
- **Yoğun Vektör (Dense):** Semantik kavram benzerliği.
- **Seyrek Vektör (BM25 Sparse):** Tam eşleşen parça numaraları, kanun maddeleri ve TCKN/vergi no filtreleri.
- **Reranker (Yeniden Sıralayıcı):** `bge-reranker-large` ile en ilgili 3-5 parçanın seçilip modele iletilmesi (token tasarrufu ve halüsinasyon engelleme).
