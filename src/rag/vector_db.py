
"""
Vector database management using FAISS (for embeddings) and SQLite 
(for metadata/relationships/image data)
"""
import os
import sqlite3
import threading
import json
import faiss
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from ..utils.config import config
import pickle
from rank_bm25 import BM25Okapi
from typing import List

# Constants for FAISS/SQLite persistence
DB_PATH = config.rag.image_db_path 
FAISS_INDEX_PATH = "./faiss_index.idx" 
ID_MAP_PATH = "./id_map.json" 
BM25_INDEX_PATH = "./bm25_index.pkl"
BM25_CORPUS_PATH = "./bm25_corpus.pkl"

class VectorDatabase:
    """Vector database manager using FAISS and SQLite"""
    
    def __init__(self):
        self.text_faiss_index = None
        self.image_faiss_index = None 
        self.text_id_map = {}
        
        self.metadata_conn = None
        self._thread_local_connections = threading.local()
        self._connection_lock = threading.Lock()
        self.bm25_index = None
        self.bm25_corpus = []
        self._load_bm25_index()
        self._initialize_metadata_db()
        self._load_faiss_indexes()

    def _get_thread_safe_connection(self):
        """Get thread-safe SQLite connection"""
        if not hasattr(self._thread_local_connections, 'conn'):
            self._thread_local_connections.conn = sqlite3.connect(
                DB_PATH,
                check_same_thread=False
            )
            self._thread_local_connections.conn.execute("PRAGMA journal_mode=WAL;")
            self._thread_local_connections.conn.execute("PRAGMA synchronous=NORMAL;")
        
        return self._thread_local_connections.conn

    def _initialize_metadata_db(self):
        """Initialize SQLite metadata database with new schema (includes Base64 data)"""
        try:
            os.makedirs(os.path.dirname(DB_PATH) or '.', exist_ok=True)
            self.metadata_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            
            cursor = self.metadata_conn.cursor()
            
            # Drop tables for a fresh, clean start
            tables_to_drop = ["images", "paragraphs", "relationships"]
            for table in tables_to_drop:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
            
            # 1. Create paragraphs table (text chunks)
            cursor.execute("""
                CREATE TABLE paragraphs (
                    id TEXT PRIMARY KEY,
                    text TEXT,
                    header TEXT,
                    page_num INTEGER,
                    source_pdf TEXT,
                    bbox_range TEXT,
                    tags TEXT,         -- JSON string of tags
                    full_page_ocr TEXT
                )
            """)

            # 2. Create images table (INCLUDES BASE64 DATA and embedding)
            cursor.execute("""
                CREATE TABLE images (
                    id TEXT PRIMARY KEY,
                    caption TEXT,
                    ocr_text TEXT,
                    data TEXT,         -- Base64 string of the image file
                    page_num INTEGER,
                    source_pdf TEXT,
                    bbox TEXT,
                    tags TEXT,         -- JSON string of tags
                    visual_embedding BLOB 
                )
            """)

            # 3. Create relationships table (for KG and structural links)
            cursor.execute("""
                CREATE TABLE relationships (
                    source_id TEXT,
                    target_id TEXT,
                    type TEXT,
                    PRIMARY KEY (source_id, target_id, type)
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX idx_para_page ON paragraphs(source_pdf, page_num)")
            cursor.execute("CREATE INDEX idx_images_page ON images(source_pdf, page_num)")
            
            self.metadata_conn.commit()
            print("[INFO] Metadata database (SQLite) initialized successfully with new schema")
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize metadata database: {e}")
            raise

    def _load_faiss_indexes(self):
        """Load FAISS index and ID maps from disk"""
        try:
            if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(ID_MAP_PATH):
                self.text_faiss_index = faiss.read_index(FAISS_INDEX_PATH)
                with open(ID_MAP_PATH, 'r') as f:
                    # Keys from JSON are strings, convert back to int
                    self.text_id_map = {int(k): v for k, v in json.load(f).items()} 
                print(f"[INFO] Loaded text FAISS index with {self.text_faiss_index.ntotal} vectors")
            else:
                print("[WARN] No existing text FAISS index found.")
        except Exception as e:
            print(f"[ERROR] Failed to load FAISS indexes: {e}")
            self.text_faiss_index = None

    
    def add_paragraph_metadata(self, props: Dict[str, Any]):
        """Add paragraph metadata to SQLite database and relationships"""
        try:
            with self._connection_lock:
                conn = self._get_thread_safe_connection()
                cursor = conn.cursor()
                
                # Insert paragraph
                cursor.execute("""
                    INSERT OR REPLACE INTO paragraphs 
                    (id, text, header, page_num, source_pdf, bbox_range, tags, full_page_ocr)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    props['id'], props['text'], props.get('header', ''), props['page_num'],
                    props['source_pdf'], str(props.get('bbox_range')),
                    json.dumps(props.get('tags', [])), props.get('full_page_ocr', '')
                ))
                
                # Add relationship: Chunk belongs to PDF
                cursor.execute("INSERT OR IGNORE INTO relationships VALUES (?, ?, ?)", 
                               (props['id'], props['source_pdf'], 'PART_OF'))
                
                # Add relationship: Chunk has Tags
                for tag in props.get('tags', []):
                    cursor.execute("INSERT OR IGNORE INTO relationships VALUES (?, ?, ?)", 
                                   (props['id'], tag, 'HAS_TAG'))
                
                conn.commit()
            
        except Exception as e:
            print(f"[ERROR] Failed to add paragraph metadata: {e}")

    def add_image_metadata(self, props: Dict[str, Any]):
        """
        Add image metadata to SQLite database, including Base64 data and embedding BLOB.
        """
        try:
            # Convert embedding list to byte array for BLOB storage
            embed_bytes = np.array(props.get('visual_embedding', []), dtype=np.float32).tobytes()

            with self._connection_lock:
                conn = self._get_thread_safe_connection()
                cursor = conn.cursor()
                
                # Insert image data, including Base64 string in 'data' column
                cursor.execute("""
                    INSERT OR REPLACE INTO images 
                    (id, caption, ocr_text, data, page_num, source_pdf, bbox, tags, visual_embedding)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    props['id'], props['caption'], props['ocr_text'], props['data'], 
                    props['page_num'], props['source_pdf'], str(props.get('bbox')),
                    json.dumps(props.get('tags', [])), sqlite3.Binary(embed_bytes)
                ))
                
                # Add relationship: Image belongs to PDF
                cursor.execute("INSERT OR IGNORE INTO relationships VALUES (?, ?, ?)", 
                               (props['id'], props['source_pdf'], 'PART_OF'))
                
                # Add relationship: Image has Tags
                for tag in props.get('tags', []):
                    cursor.execute("INSERT OR IGNORE INTO relationships VALUES (?, ?, ?)", 
                                   (props['id'], tag, 'HAS_TAG'))
                
                conn.commit()
            
        except Exception as e:
            print(f"[ERROR] Failed to add image metadata: {e}")


    # --- FAISS Management Methods ---

    def save_text_faiss_index(self, embeddings: np.ndarray, all_paragraphs: List[Dict]):
        """Build and save the text FAISS index and ID map"""
        try:
            if not embeddings.size:
                print("[WARN] No embeddings to save. Skipping FAISS index creation.")
                self.text_faiss_index = None
                return False
                
            embedding_dim = embeddings.shape[1]
            index = faiss.IndexFlatIP(embedding_dim) 
            index.add(embeddings)
            
            id_map = {
                i: {
                    "paragraph_id": p["id"],
                    "text": p["text"],
                    "source_pdf": p["source_pdf"],
                    "page_num": p["page_num"]
                }
                for i, p in enumerate(all_paragraphs)
            }
            
            faiss.write_index(index, FAISS_INDEX_PATH)
            with open(ID_MAP_PATH, 'w') as f:
                json.dump(id_map, f)
            
            self.text_faiss_index = index
            self.text_id_map = id_map
            print(f"[INFO] Text FAISS index saved successfully with {index.ntotal} vectors.")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save text FAISS index: {e}")
            return False

    def query_text(self, query_embedding: np.ndarray, n_results: int = 10) -> List[Dict]:
        """Query text FAISS index and return metadata"""
        if self.text_faiss_index is None:
            return []
        
        try:
            # Ensure input is a numpy array of float32
            if not isinstance(query_embedding, np.ndarray):
                query_embedding = np.array(query_embedding, dtype=np.float32)
            
            if query_embedding.ndim == 1:
                query_embedding = query_embedding.reshape(1, -1)
                
            D, I = self.text_faiss_index.search(query_embedding, k=n_results)
            
            results = []
            for i, d in zip(I[0], D[0]):
                if i in self.text_id_map:
                    meta = self.text_id_map[i].copy()
                    meta['distance'] = float(d)
                    meta['id'] = meta.pop('paragraph_id')
                    results.append(meta)
            return results
        except Exception as e:
            print(f"[ERROR] Failed to query text FAISS index: {e}")
            return []

    def _load_bm25_index(self):
        """Load BM25 index from disk"""
        try:
            if os.path.exists(BM25_INDEX_PATH) and os.path.exists(BM25_CORPUS_PATH):
                with open(BM25_INDEX_PATH, 'rb') as f:
                    self.bm25_index = pickle.load(f)
                with open(BM25_CORPUS_PATH, 'rb') as f:
                    self.bm25_corpus = pickle.load(f)
                print(f"[INFO] Loaded BM25 index with {len(self.bm25_corpus)} documents")
        except Exception as e:
            print(f"[WARN] No BM25 index found: {e}")
    
    def save_bm25_index(self, all_paragraphs: List[Dict]):
        """Build and save BM25 index"""
        try:
            tokenized_corpus = [p['text'].lower().split() for p in all_paragraphs]
            self.bm25_index = BM25Okapi(tokenized_corpus)
            self.bm25_corpus = all_paragraphs
            
            with open(BM25_INDEX_PATH, 'wb') as f:
                pickle.dump(self.bm25_index, f)
            with open(BM25_CORPUS_PATH, 'wb') as f:
                pickle.dump(self.bm25_corpus, f)
            
            print(f"[INFO] BM25 index saved with {len(tokenized_corpus)} documents")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save BM25 index: {e}")
            return False
    
    def query_bm25(self, query: str, n_results: int = 10) -> List[Dict]:
        """Query BM25 index"""
        if not self.bm25_index or not self.bm25_corpus:
            return []
        
        tokenized_query = query.lower().split()
        scores = self.bm25_index.get_scores(tokenized_query)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:n_results]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include non-zero scores
                doc = self.bm25_corpus[idx].copy()
                doc['bm25_score'] = float(scores[idx])
                results.append(doc)
        
        return results

    # --- Collection Counts ---
    
    def get_text_collection_count(self) -> int:
        """Get number of paragraphs (text chunks)"""
        return self.text_faiss_index.ntotal if self.text_faiss_index else 0
    
    def get_image_collection_count(self) -> int:
        """Get number of images from SQLite metadata table"""
        try:
            with self._connection_lock:
                return self._get_thread_safe_connection().execute("SELECT COUNT(*) FROM images").fetchone()[0]
        except: return 0
    
    def close(self):
        """Close database connections"""
        if self.metadata_conn: self.metadata_conn.close()
        if hasattr(self._thread_local_connections, 'conn'): self._thread_local_connections.conn.close()