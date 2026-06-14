import os
import sys

# Add the project root to sys.path so that 'app.services...' imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.services.retrieval_module import RetrievalModule

rm = RetrievalModule()
print(f"Total documents in collection: {rm.vector_store._collection.count()}")

query = "드론 충돌 회피 시스템 - 센서 오류로 인해 장애물을 탐지하지 못할 경우 발생할 수 있는 위험"
results = rm.vector_store.similarity_search_with_score(query, k=5)

for doc, distance in results:
    print(f"Distance: {distance}, Similarity: {1.0 - distance}")
