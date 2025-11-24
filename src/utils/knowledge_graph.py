
import sqlite3
import json
from typing import List, Dict, Any

class KnowledgeGraphLoader:
    """Handles loading and querying the knowledge graph and relationships from SQLite."""
    
    def __init__(self, vector_db): 
        # vector_db will be the instance of the new VectorDatabase class
        self.vector_db = vector_db
        
    def load_knowledge_graph(self, pdf_paths: List[str]) -> Dict[str, Any]:
        """
        Loads HAS_TAG relationships for the given PDFs.
        Returns a dictionary where keys are PDF names and values are sets of tagged paragraphs.
        """
        kg = {}
        if not pdf_paths: return kg
            
        try:
            with self.vector_db._connection_lock:
                conn = self.vector_db._get_thread_safe_connection()
                cursor = conn.cursor()
                
                placeholders = ', '.join(['?'] * len(pdf_paths))
                # Query relationships and join with paragraphs to get the PDF source
                query = f"""
                    SELECT r.source_id, p.source_pdf
                    FROM relationships r
                    JOIN paragraphs p ON r.source_id = p.id
                    WHERE r.type = 'HAS_TAG' AND p.source_pdf IN ({placeholders})
                """
                
                results = cursor.execute(query, pdf_paths).fetchall()
                
                for source_id, source_pdf in results:
                    if source_pdf not in kg:
                        kg[source_pdf] = {'tagged_paragraphs': set()} 
                    kg[source_pdf]['tagged_paragraphs'].add(source_id)
                    
            return kg
        except Exception as e:
            print(f"[ERROR] Failed to load KG: {e}")
            return {}

    def get_paragraph_tags(self, paragraph_id: str) -> List[str]:
        """Retrieve tags for a specific paragraph ID."""
        try:
            with self.vector_db._connection_lock:
                conn = self.vector_db._get_thread_safe_connection()
                cursor = conn.cursor()
                result = cursor.execute("SELECT tags FROM paragraphs WHERE id = ?", (paragraph_id,)).fetchone()
                if result and result[0]:
                    # Tags are stored as a JSON string
                    return json.loads(result[0])
            return []
        except Exception as e:
            print(f"[ERROR] Failed to get paragraph tags: {e}")
            return []