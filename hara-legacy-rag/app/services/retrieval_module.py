import os
import re
import hashlib
import shutil
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

CHROMADB_DIR    = "./chroma_db_retrieval_module"
COLLECTION_NAME = "aero_safety_knowledge_rag_cosine"
EMBED_MODEL     = "text-embedding-3-small"
DATASET_PATH    = "./data/aero_safety_knowledge_rag_v2.txt"


class RetrievalModule:

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
        # ── 초기화 전에 재초기화 필요 여부를 먼저 판단 ──────────────────────
        # Chroma 인스턴스를 열기 전에 판단해야 Windows 파일 잠금을 피할 수 있음
        need_reset = self._need_reset()

        if need_reset and os.path.exists(CHROMADB_DIR):
            # Chroma를 아직 열지 않은 상태이므로 안전하게 삭제 가능
            shutil.rmtree(CHROMADB_DIR)
            print("RetrievalModule: 기존 ChromaDB 디렉터리 삭제 완료.")

        self.vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=CHROMADB_DIR,
            collection_metadata={"hnsw:space": "cosine"},
        )
        self._initialize_dataset(force=need_reset)

    # ── 데이터셋 해시 ─────────────────────────────────────────────────────────
    @staticmethod
    def _dataset_hash(path: str) -> str:
        h = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    # ── Chroma를 열기 전에 재초기화 필요 여부 판단 ───────────────────────────
    def _need_reset(self) -> bool:
        """
        Chroma 인스턴스를 열기 전에 재초기화가 필요한지 판단한다.
        판단 기준:
          1) ChromaDB 디렉터리 자체가 없음 → 최초 실행
          2) 해시 파일이 없음 (구버전 컬렉션) → 재초기화
          3) 데이터셋 파일과 저장된 해시가 다름 → 재초기화
        """
        if not os.path.exists(DATASET_PATH):
            raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")

        hash_file = os.path.join(CHROMADB_DIR, ".dataset_hash")

        # ChromaDB 디렉터리 없음 → 최초 실행
        if not os.path.exists(CHROMADB_DIR):
            return True

        # 해시 파일 없음 → 구버전 컬렉션
        if not os.path.exists(hash_file):
            return True

        # 해시 비교
        current_hash = self._dataset_hash(DATASET_PATH)
        with open(hash_file, "r") as f:
            stored_hash = f.read().strip()

        if current_hash != stored_hash:
            print(f"RetrievalModule: 데이터셋 변경 감지 "
                  f"(저장:{stored_hash[:8]}... → 현재:{current_hash[:8]}...)")
            return True

        return False

    # ── 텍스트 추출 (유사도 향상을 위해 정보 보강) ───────────────────────────────────────────────────
    @staticmethod
    def _extract_search_text(category: str, pattern: str, scenario_tag: str, context: str) -> str:
        # 카테고리, 패턴, 태깅, 본문 전체를 합쳐 하나의 구조화된 텍스트로 만들어 임베딩 유사도를 극대화
        return f"[Category: {category}] [Pattern: {pattern}] [Tag: {scenario_tag}]\n{context}".strip()

    # ── 인덱싱 ───────────────────────────────────────────────────────────────
    def _initialize_dataset(self, force: bool = False):
        existing_count = self.vector_store._collection.count()

        if not force and existing_count > 0:
            print(f"RetrievalModule: 컬렉션 최신 상태 ({existing_count}건). "
                  f"초기화 생략.")
            return

        print(f"RetrievalModule: 데이터셋 로드 중 ({DATASET_PATH})...")
        docs = []
        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines[2:]:
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) < 4:
                continue

            doc_id       = parts[0]
            category     = parts[1]
            pattern      = parts[2]
            context      = parts[3]
            scenario_tag = parts[4] if len(parts) >= 5 else ""

            docs.append(Document(
                page_content=self._extract_search_text(category, pattern, scenario_tag, context),
                metadata={
                    "id":       doc_id,
                    "category": category,
                    "pattern":  pattern,
                    "context":  context,
                },
            ))

        if not docs:
            print("RetrievalModule: 유효한 데이터가 없습니다.")
            return

        print(f"RetrievalModule: {len(docs)}건 인덱싱 중...")
        self.vector_store.add_documents(docs)

        # 해시를 별도 파일로 저장 (컬렉션 메타데이터 대신 사용)
        # → Chroma 버전 호환성 문제 없이 안정적으로 작동
        current_hash = self._dataset_hash(DATASET_PATH)
        hash_file = os.path.join(CHROMADB_DIR, ".dataset_hash")
        with open(hash_file, "w") as f:
            f.write(current_hash)

        print(f"RetrievalModule: 초기화 완료. (hash={current_hash[:8]}...)")

    # ── 검색 ─────────────────────────────────────────────────────────────────
    def search_top_k(self, query: str, k: int = 5, threshold: float = 0.50):
        results = self.vector_store.similarity_search_with_score(query, k=k)

        retrieved = []
        for doc, distance in results:
            similarity = max(0.0, 1.0 - distance)
            if similarity >= threshold:
                retrieved.append({
                    "document":         doc,
                    "similarity_score": round(similarity, 4),
                    "raw_distance":     round(distance, 4),
                })

        retrieved.sort(key=lambda x: x["similarity_score"], reverse=True)
        return retrieved