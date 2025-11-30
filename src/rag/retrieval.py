"""
Retrieval functionality for RAG system (Hybrid MMR/KG/CLIP Enhanced)
"""
import os
import torch
import numpy as np
import json
import base64
from typing import List, Dict, Any, Tuple, Set
from .vector_db import VectorDatabase
from ..utils.config import config
from ..utils.mmr_ranker import MMRRanker
from ..utils.knowledge_graph import KnowledgeGraphLoader
from ..utils.graph_retrieval import GraphRetrieval
class RetrievalSystem:
    """Hybrid retrieval system for text and images"""
    
    def __init__(self, vector_db: VectorDatabase):
        self.vector_db = vector_db
        self.mmr_ranker = MMRRanker()
        self.kg_loader = KnowledgeGraphLoader(self.vector_db)

    def retrieve_text(self, query: str, text_embedder, top_k: int = 5, 
                     fetch_k: int = 15, diversity: float = 0.6) -> Tuple[List[str], List[Dict]]:
        """Retrieve relevant text chunks with KG boost and MMR reranking"""
        try:
            query_emb = text_embedder.encode(
                query, 
                normalize_embeddings=True,
                convert_to_tensor=False
            )
            query_emb = np.array(query_emb, dtype=np.float32).reshape(1, -1)
            
            results = self.vector_db.query_text(
                query_embedding=query_emb,
                n_results=fetch_k
            ) 
            
            if not results: return [], []
            
            kg_enhanced_results = []
            pdf_paths = list(set([r.get('source_pdf', '') for r in results]))
            kg = self.kg_loader.load_knowledge_graph(pdf_paths)
            
            for result in results:
                result['kg_score'] = 0.0
                if result.get('source_pdf') in kg:
                    tags = self.kg_loader.get_paragraph_tags(result['id'])
                    query_words = set(query.lower().split())
                    common_words = query_words.intersection(set(tags))
                    if common_words:
                        result['kg_score'] += 0.2
                
                result['score'] = (1.0 - result.get('distance', 1.0)) + result['kg_score']
                kg_enhanced_results.append(result)
            
            doc_texts = [r['text'] for r in kg_enhanced_results]
            doc_embs = text_embedder.encode(doc_texts, convert_to_tensor=False)
            doc_embs = np.array(doc_embs, dtype=np.float32)
            
            selected_ids = self.mmr_ranker.calculate_mmr(
                query_emb.flatten(), 
                doc_embs, 
                [r['id'] for r in kg_enhanced_results], 
                top_k, 
                diversity
            )
            
            final_results = [r for r in kg_enhanced_results if r['id'] in selected_ids]
            selected_docs = [r['text'] for r in final_results]
            selected_metas = [{'source': r['source_pdf'], 'page': r['page_num'], 'id': r['id']} for r in final_results]

            # NEW: Graph expansion
            try:
                graph = GraphRetrieval(self.vector_db)
                initial_ids = [r['id'] for r in final_results]
                expanded_ids = graph.expand_results(initial_ids, max_expansion=2)
                
                # Fetch expanded chunks
                if len(expanded_ids) > len(initial_ids):
                    with self.vector_db._connection_lock:
                        conn = self.vector_db._get_thread_safe_connection()
                        cursor = conn.cursor()
                        
                        placeholders = ','.join('?' * len(expanded_ids))
                        expanded_results = cursor.execute(f"""
                            SELECT id, text, source_pdf, page_num
                            FROM paragraphs
                            WHERE id IN ({placeholders})
                        """, expanded_ids).fetchall()
                        
                        # Add new chunks
                        for row in expanded_results:
                            para_id, text, source_pdf, page_num = row
                            if para_id not in initial_ids:
                                selected_docs.append(text)
                                selected_metas.append({
                                    'source': source_pdf,
                                    'page': page_num,
                                    'id': para_id
                                })
                    
                    print(f"[INFO] Graph expanded results from {len(initial_ids)} to {len(selected_docs)} chunks")
            except Exception as e:
                print(f"[WARN] Graph expansion failed: {e}")

            return selected_docs, selected_metas
            
        except Exception as e:
            print(f"[ERROR] Text retrieval failed: {e}")
            return [], []

    def extract_pages_from_text_metadata(self, text_metas: List[Dict]) -> Set[int]:
        pages = set()
        for meta in text_metas:
            if "page" in meta and isinstance(meta["page"], int):
                pages.add(meta["page"])
        return pages

    def retrieve_images_hybrid(self, query: str, clip_model, clip_processor, 
                              text_embedder, retrieved_text_pages: Set[int] = None, 
                              top_k: int = 3) -> List[str]:
        """
        Hybrid image retrieval:
        1. Semantic Search (CLIP): Matches query meaning to image visual content.
        2. Keyword Search: Matches query words to OCR text.
        3. Context Boost: Boosts images on pages where relevant text was found.
        """
        try:
            # --- 1. Generate CLIP Text Embedding for the Query ---
            # This converts your text "carbohydrates" into a visual vector
            inputs = clip_processor(text=[query], return_tensors="pt", padding=True)
            with torch.no_grad():
                query_features = clip_model.get_text_features(**inputs)
                # Normalize for cosine similarity
                query_features = query_features / query_features.norm(p=2, dim=-1, keepdim=True)
                query_emb = query_features.cpu().numpy().flatten()

            # --- 2. Fetch All Images & Embeddings from SQLite ---
            # We fetch everything because SQLite is fast enough for typical local usage
            search_term = f"%{query.lower().replace(' ', '%')}%"
            
            with self.vector_db._connection_lock:
                conn = self.vector_db._get_thread_safe_connection()
                cursor = conn.cursor()
                # Get basic data + visual embedding
                sql_query = """
                    SELECT id, caption, ocr_text, data, page_num, source_pdf, visual_embedding
                    FROM images
                """
                results = cursor.execute(sql_query).fetchall()
            
            if not results:
                return []

            ranked_images = []
            
            for row in results:
                img_id, caption, ocr_text, data, page_num, source_pdf, vis_emb_bytes = row
                
                # -- Score A: Semantic Similarity (CLIP) --
                semantic_score = 0.0
                if vis_emb_bytes:
                    # Convert BLOB back to numpy array
                    img_emb = np.frombuffer(vis_emb_bytes, dtype=np.float32)
                    # Cosine similarity
                    semantic_score = float(np.dot(query_emb, img_emb))
                
                # -- Score B: Keyword Match (OCR) --
                text_score = 0.0
                full_text = (str(caption) + " " + str(ocr_text)).lower()
                if query.lower() in full_text:
                    text_score = 0.3  # Bonus for exact word match
                
                # -- Score C: Page Proximity --
                proximity_score = 0.0
                if retrieved_text_pages and page_num is not None:
                    min_distance = min(abs(page_num - p) for p in retrieved_text_pages)
                    if min_distance <= config.rag.page_context_window:
                        proximity_score = 0.2 * (1.0 - (min_distance / (config.rag.page_context_window + 1)))
                
                # Combine Scores
                # If semantic score is high (e.g. > 0.22), it's likely a relevant image
                final_score = semantic_score + text_score + proximity_score
                
                # Threshold filter (Lowered to 0.2 to catch more images)
                if final_score > 0.2:
                    ranked_images.append({
                        'id': img_id,
                        'data': data,
                        'page_num': page_num,
                        'source_pdf': source_pdf,
                        'score': final_score
                    })
            
            # 3. Sort by Score
            ranked_images.sort(key=lambda x: x["score"], reverse=True)
            top_images = ranked_images[:top_k]
            
            # 4. Restore Images to Files
            final_image_paths = []
            for img in top_images:
                try:
                    if not img['data']: continue
                    img_bytes = base64.b64decode(img['data'])
                    
                    save_dir = os.path.join(config.rag.image_dir, img['source_pdf'], f"page_{img['page_num']}")
                    os.makedirs(save_dir, exist_ok=True)
                    file_path = os.path.join(save_dir, f"{img['id']}.png")
                    
                    # Only write if it doesn't exist to save time
                    if not os.path.exists(file_path):
                        with open(file_path, "wb") as f:
                            f.write(img_bytes)
                    
                    final_image_paths.append(file_path)
                except Exception as e:
                    print(f"[WARN] Failed to restore image {img['id']}: {e}")
                    
            return final_image_paths
            
        except Exception as e:
            print(f"[ERROR] Image retrieval failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    def retrieve_images_simplified(self, query: str, text_embedder, 
                               retrieved_text_pages: Set[int] = None, 
                               top_k: int = 3) -> List[str]:
        """
        Simplified image retrieval using TF-IDF on surrounding text.
        No CLIP dependency - uses context matching only.
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Fetch all images
            with self.vector_db._connection_lock:
                conn = self.vector_db._get_thread_safe_connection()
                cursor = conn.cursor()
                results = cursor.execute("""
                    SELECT id, caption, ocr_text, data, page_num, source_pdf
                    FROM images
                """).fetchall()
            
            if not results:
                return []
            
            # Build corpus for TF-IDF
            corpus = [query]  # First doc is query
            image_data = []
            
            for row in results:
                img_id, caption, ocr_text, data, page_num, source_pdf = row
                
                # Combine image text with surrounding paragraph text
                image_text = f"{caption or ''} {ocr_text or ''}"
                
                # Get text from same page
                para_results = cursor.execute("""
                    SELECT text FROM paragraphs
                    WHERE source_pdf = ? AND page_num = ?
                    LIMIT 3
                """, (source_pdf, page_num)).fetchall()
                
                surrounding_text = " ".join([p[0] for p in para_results])
                combined_text = f"{image_text} {surrounding_text}"
                
                corpus.append(combined_text)
                image_data.append({
                    'id': img_id,
                    'data': data,
                    'page_num': page_num,
                    'source_pdf': source_pdf
                })
            
            # Compute TF-IDF similarity
            try:
                vectorizer = TfidfVectorizer(
                    max_features=500,
                    stop_words='english',
                    ngram_range=(1, 2)
                )
                tfidf_matrix = vectorizer.fit_transform(corpus)
                query_vec = tfidf_matrix[0:1]
                doc_vecs = tfidf_matrix[1:]
                
                similarities = cosine_similarity(query_vec, doc_vecs).flatten()
            except ValueError:
                return []
            
            # Score images
            scored_images = []
            for i, img in enumerate(image_data):
                score = float(similarities[i])
                
                # Proximity boost: if on same page as retrieved text
                if retrieved_text_pages and img['page_num'] in retrieved_text_pages:
                    score += 0.3
                
                # Single threshold
                if score > 0.15:
                    scored_images.append((score, img))
            
            # Sort and take top-k
            scored_images.sort(reverse=True, key=lambda x: x[0])
            top_images = [img for _, img in scored_images[:top_k]]
            
            # Restore to disk
            final_paths = []
            for img in top_images:
                try:
                    if not img['data']:
                        continue
                    
                    img_bytes = base64.b64decode(img['data'])
                    save_dir = os.path.join(
                        config.rag.image_dir,
                        img['source_pdf'],
                        f"page_{img['page_num']}"
                    )
                    os.makedirs(save_dir, exist_ok=True)
                    file_path = os.path.join(save_dir, f"{img['id']}.png")
                    
                    if not os.path.exists(file_path):
                        with open(file_path, "wb") as f:
                            f.write(img_bytes)
                    
                    final_paths.append(file_path)
                except Exception as e:
                    print(f"[WARN] Failed to restore image: {e}")
            
            return final_paths
            
        except Exception as e:
            print(f"[ERROR] Image retrieval failed: {e}")
            import traceback
            traceback.print_exc()
            return []    
    
    def retrieve_multimodal(self, query: str, text_embedder, clip_model, clip_processor, 
                           text_top_k: int = 5, image_top_k: int = None) -> Tuple[List[str], List[Dict], List[str]]:
        if image_top_k is None: image_top_k = config.rag.max_images_returned
        
        text_docs, text_metas = self.retrieve_text(query, text_embedder, text_top_k)
        retrieved_pages = self.extract_pages_from_text_metadata(text_metas)
        
        """image_paths = self.retrieve_images_hybrid(
            query=query,
            clip_model=clip_model,
            clip_processor=clip_processor,
            text_embedder=text_embedder,
            retrieved_text_pages=retrieved_pages,
            top_k=image_top_k
        )"""
        image_paths = self.retrieve_images_simplified(
            query=query,
            text_embedder=text_embedder,
            retrieved_text_pages=retrieved_pages,
            top_k=image_top_k
        )
        
        return text_docs, text_metas, image_paths