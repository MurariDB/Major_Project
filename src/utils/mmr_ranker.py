
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any

class MMRRanker:
    """Maximal Marginal Relevance implementation for diverse document selection"""
    
    def __init__(self, lambda_param: float = 0.6):
        self.lambda_param = lambda_param 

    def calculate_mmr(self, query_embedding: np.ndarray, document_embeddings: np.ndarray, 
                     document_ids: List[str], k: int, diversity: float = 0.6) -> List[str]:
        """
        Calculate MMR to select diverse and relevant documents.
        """
        if document_embeddings.shape[0] == 0:
            return []
        
        self.lambda_param = diversity 
        query_emb_reshaped = query_embedding.reshape(1, -1)
        
        # Calculate relevance scores (cosine similarity with query)
        relevance_scores = cosine_similarity(query_emb_reshaped, document_embeddings)[0]
        
        selected_indices = []
        remaining_indices = list(range(len(document_embeddings)))
        
        # 1. Select first document with highest relevance
        first_idx = np.argmax(relevance_scores)
        selected_indices.append(first_idx)
        remaining_indices.remove(first_idx)
        
        # 2. Select remaining documents using MMR formula
        while len(selected_indices) < min(k, document_embeddings.shape[0]) and remaining_indices:
            mmr_scores = []
            
            for idx in remaining_indices:
                relevance = relevance_scores[idx]
                
                # Diversity component (maximum similarity to already selected)
                selected_embeddings = [document_embeddings[i] for i in selected_indices]
                similarity_to_selected = cosine_similarity(
                    document_embeddings[idx].reshape(1, -1), selected_embeddings
                )[0]
                max_similarity = np.max(similarity_to_selected)
                
                # MMR formula: λ * relevance - (1-λ) * redundancy
                mmr_score = self.lambda_param * relevance - (1 - self.lambda_param) * max_similarity
                mmr_scores.append((mmr_score, idx))
            
            # Select document with highest MMR score
            best_score, best_idx = max(mmr_scores)
            selected_indices.append(best_idx)
            remaining_indices.remove(best_idx)
        
        return [document_ids[i] for i in selected_indices]