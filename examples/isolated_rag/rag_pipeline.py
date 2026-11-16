#!/usr/bin/env python3
"""
İzole Kurumsal RAG Örnek Uygulaması (Isolated Enterprise RAG Example)
Harici hiçbir bulut servisine bağlanmadan, yerel dokümanları indeksler,
anahtar kelime & semantik benzerlik ile en alakalı içeriği bulur ve
yerel dil modeline verilecek güvenli istemi (prompt) üretir.
"""

import os
import re
import math
from typing import List, Dict, Tuple

class SimpleLocalRAG:
    def __init__(self):
        self.documents = []
        self.doc_vectors = []
        self.vocabulary = {}

    def _tokenize(self, text: str) -> List[str]:
        # Temel Türkçe ve evrensel harf ayrıştırma
        return re.findall(r'\b[a-zA-ZçğıöşüÇĞİÖŞÜ0-9_]{3,}\b', text.lower())

    def add_document(self, doc_id: str, title: str, content: str, clearance: str = "GENEL"):
        tokens = self._tokenize(content)
        term_freq = {}
        for token in tokens:
            term_freq[token] = term_freq.get(token, 0) + 1
            if token not in self.vocabulary:
                self.vocabulary[token] = len(self.vocabulary)
        
        self.documents.append({
            "id": doc_id,
            "title": title,
            "content": content,
            "clearance": clearance,
            "term_freq": term_freq,
            "length": len(tokens)
        })

    def search(self, query: str, user_clearance: str = "GENEL", top_k: int = 2) -> List[Dict]:
        query_tokens = self._tokenize(query)
        scores: List[Tuple[float, Dict]] = []

        for doc in self.documents:
            # RBAC Gizlilik Seviyesi Kontrolü
            if doc["clearance"] == "GİZLİ" and user_clearance != "GİZLİ":
                continue # Yetkisiz kullanıcıya dokümanı gösterme

            score = 0.0
            for qt in query_tokens:
                if qt in doc["term_freq"]:
                    # Basit TF puanı
                    tf = doc["term_freq"][qt] / (doc["length"] + 1e-5)
                    score += tf

            if score > 0:
                scores.append((score, doc))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scores[:top_k]]

    def generate_context_prompt(self, user_query: str, user_clearance: str = "GENEL") -> str:
        relevant_docs = self.search(user_query, user_clearance=user_clearance)
        if not relevant_docs:
            context_block = "[İlgili iç ağ dokümanı bulunamadı]"
        else:
            context_block = "\n\n".join([
                f"--- DOKÜMAN [{d['id']}: {d['title']}] (Gizlilik: {d['clearance']}) ---\n{d['content']}"
                for d in relevant_docs
            ])

        prompt = (
            "Sen şirket içi çalışan izole bir yapay zeka asistanısın.\n"
            "Aşağıdaki güvenli şirket içi dokümanları referans alarak soruyu cevapla.\n\n"
            f"[KURUMSAL BAĞLAM]:\n{context_block}\n\n"
            f"[KULLANICI SORUSU]: {user_query}\n\n"
            "[İZÔLE MODEL YANITI]:"
        )
        return prompt

if __name__ == "__main__":
    rag = SimpleLocalRAG()
    
    # Şirket içi örnek dokümanları yükle
    rag.add_document(
        doc_id="POL-01",
        title="Kurumsal Veri İletişim Prosedürü",
        content="Şirket içi hassas müşteri verileri ve kaynak kodları asla internete açık harici API'lere yüklenemez. Tüm işlemler yerel ağdaki İzole YZ Ağ Geçidi üzerinden yürütülür.",
        clearance="GENEL"
    )
    rag.add_document(
        doc_id="ARGE-99",
        title="Otonom Sistemler Donanım Mimarisi",
        content="KAM projesi kapsamında kullanılan gömülü NPU üniteleri, 15W güç tüketiminde 30 TOPS işlem gücü sağlamaktadır. Harici haberleşme antenleri operasyon sırasında fiziksel olarak kapatılır.",
        clearance="GİZLİ"
    )

    print("=" * 64)
    print(" 🛡️  İZÔLE RAG SİSTEMİ DEMO ÇALIŞMASI")
    print("=" * 64)

    # 1. Standart Kullanıcı Sorgusu
    soru1 = "Hassas müşteri verilerini nasıl işlemeliyiz?"
    print(f"\n1. Kullanıcı Sorgusu: '{soru1}' (Yetki: GENEL)")
    p1 = rag.generate_context_prompt(soru1, user_clearance="GENEL")
    print("-" * 50)
    print(p1)

    # 2. Yetkisiz Gizli Doküman Arama Denemesi
    soru2 = "KAM projesinde kullanılan gömülü NPU gücü nedir?"
    print(f"\n2. Kullanıcı Sorgusu: '{soru2}' (Yetki: GENEL - Yetersiz)")
    p2 = rag.generate_context_prompt(soru2, user_clearance="GENEL")
    print("-" * 50)
    print(p2)

    # 3. Yetkili Kullanıcı Arama
    print(f"\n3. Kullanıcı Sorgusu: '{soru2}' (Yetki: GİZLİ - Tam Yetkili)")
    p3 = rag.generate_context_prompt(soru2, user_clearance="GİZLİ")
    print("-" * 50)
    print(p3)
