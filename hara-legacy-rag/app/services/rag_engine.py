from app.services.retrieval_module import RetrievalModule

TOP_K = 5

class RAGEngine:
    def __init__(self):
        self.retrieval_module = RetrievalModule()

    def format_docs(self, docs):
        """
        LLM에 전달할 Knowledge Context 텍스트를 조립한다.

        [수정] page_content → metadata["context"] 사용
        - page_content: 검색용 짧은 텍스트 (Scenario Tag + 첫 문장)
        - metadata["context"]: NTSB 사고 분석·안전 교훈이 담긴 전체 원문
        LLM에는 반드시 전체 원문을 전달해야 풍부한 근거 기반 분석이 가능하다.
        """
        parts = []
        for i, res in enumerate(docs):
            doc   = res["document"]
            score = res["similarity_score"]
            meta  = doc.metadata or {}

            full_context = meta.get("context", doc.page_content)  # ← 핵심 수정

            header = (
                f"[Related Knowledge {i+1}: "
                f"ID={meta.get('id', '?')}, "
                f"Category={meta.get('category', '?')}, "
                f"Pattern={meta.get('pattern', '?')}, "
                f"Similarity={score}]"
            )
            parts.append(header + "\n" + full_context)

        return "\n\n".join(parts)

    def retrieve_context(self, query: str, top_k: int = TOP_K, threshold: float = 0.50):
        """
        Search for top_k relevant contexts for the given query.
        """
        results = self.retrieval_module.search_top_k(query, k=top_k, threshold=threshold)

        # LLM에 주입할 전체 텍스트 블록
        context_text = self.format_docs(results)

        # 프론트엔드 표시용 source_docs (기존 구조 유지)
        source_docs = []
        for res in results:
            doc   = res["document"]
            score = res["similarity_score"]
            meta  = doc.metadata or {}
            source_docs.append({
                "content": meta.get("context", doc.page_content),  # ← 수정
                "metadata": {
                    "id":       meta.get("id",       "?"),
                    "category": meta.get("category", "?"),
                    "pattern":  meta.get("pattern",  "?"),
                    "score":    score,
                }
            })
            print("score", score);
        return context_text, source_docs