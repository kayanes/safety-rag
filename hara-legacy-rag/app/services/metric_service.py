import json
from app.services.parser_service import ParserService
from langchain_openai import OpenAIEmbeddings
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class MetricService:
    _embeddings = None

    @classmethod
    def get_embeddings(cls):
        if cls._embeddings is None:
            cls._embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        return cls._embeddings

    @staticmethod
    def evaluate_result(text: str, ground_truth: str = None):
        structure_info = ParserService.check_structure(text)
        parsed_rows = ParserService.extract_hara_table(text)
        
        similarity_score = 0.0
        if ground_truth:
            try:
                embeddings = MetricService.get_embeddings()
                # Generate embeddings
                vec_text = embeddings.embed_query(text)
                vec_gt = embeddings.embed_query(ground_truth)
                
                # Calculate Cosine Similarity
                similarity_score = cosine_similarity([vec_text], [vec_gt])[0][0]
                similarity_score = float(similarity_score) # Convert to float
            except Exception as e:
                print(f"Error calculating similarity: {e}")
                similarity_score = 0.0

        metrics = {
            "structureScore": structure_info["score"],
            "complianceDetails": structure_info["details"],
            "cosineSimilarity": similarity_score,
            "rowCount": len(parsed_rows)
        }
        
        return metrics, parsed_rows
