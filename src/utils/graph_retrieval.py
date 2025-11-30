"""
Graph-based retrieval expansion using NetworkX
"""
import sqlite3
import json
from typing import List, Dict, Set
from collections import defaultdict
import networkx as nx

class GraphRetrieval:
    """Use KG to expand and enhance retrieval results"""
    
    def __init__(self, vector_db):
        self.vector_db = vector_db
        self.graph = None
    
    def build_graph(self):
        """Build entity graph from SQLite relationships"""
        self.graph = nx.Graph()
        
        with self.vector_db._connection_lock:
            conn = self.vector_db._get_thread_safe_connection()
            cursor = conn.cursor()
            
            # Add paragraph nodes with tags
            paragraphs = cursor.execute("""
                SELECT id, page_num, source_pdf, tags 
                FROM paragraphs
            """).fetchall()
            
            for para_id, page_num, source_pdf, tags_json in paragraphs:
                tags = json.loads(tags_json) if tags_json else []
                self.graph.add_node(
                    para_id,
                    type='paragraph',
                    page=page_num,
                    pdf=source_pdf
                )
                
                # Link to entities
                for tag in tags:
                    self.graph.add_node(tag, type='entity')
                    self.graph.add_edge(para_id, tag)
            
            # Add image nodes with tags
            images = cursor.execute("""
                SELECT id, page_num, source_pdf, tags 
                FROM images
            """).fetchall()
            
            for img_id, page_num, source_pdf, tags_json in images:
                tags = json.loads(tags_json) if tags_json else []
                self.graph.add_node(
                    img_id,
                    type='image',
                    page=page_num,
                    pdf=source_pdf
                )
                
                for tag in tags:
                    self.graph.add_node(tag, type='entity')
                    self.graph.add_edge(img_id, tag)
        
        print(f"[INFO] Built KG: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
    
    def expand_results(self, initial_chunk_ids: List[str], max_expansion: int = 2) -> List[str]:
        """Expand retrieval by finding related chunks via shared entities"""
        if not self.graph:
            self.build_graph()
        
        # Find entities connected to initial results
        connected_entities = set()
        for chunk_id in initial_chunk_ids:
            if chunk_id in self.graph:
                for neighbor in self.graph.neighbors(chunk_id):
                    if self.graph.nodes[neighbor].get('type') == 'entity':
                        connected_entities.add(neighbor)
        
        # Find other paragraphs mentioning same entities
        expanded = set(initial_chunk_ids)
        for entity in connected_entities:
            if entity in self.graph:
                for neighbor in self.graph.neighbors(entity):
                    if self.graph.nodes[neighbor].get('type') == 'paragraph':
                        expanded.add(neighbor)
                        if len(expanded) >= len(initial_chunk_ids) + max_expansion:
                            break
        
        return list(expanded)
    
    def find_related_images(self, chunk_ids: List[str], top_k: int = 3) -> List[str]:
        """Find images related to chunks via shared entities"""
        if not self.graph:
            self.build_graph()
        
        # Collect entities from chunks
        entities = set()
        for chunk_id in chunk_ids:
            if chunk_id in self.graph:
                for neighbor in self.graph.neighbors(chunk_id):
                    if self.graph.nodes[neighbor].get('type') == 'entity':
                        entities.add(neighbor)
        
        # Score images by entity overlap
        image_scores = defaultdict(float)
        for entity in entities:
            if entity in self.graph:
                for neighbor in self.graph.neighbors(entity):
                    if self.graph.nodes[neighbor].get('type') == 'image':
                        image_scores[neighbor] += 1.0
        
        # Return top images
        ranked = sorted(image_scores.items(), key=lambda x: x[1], reverse=True)
        return [img_id for img_id, _ in ranked[:top_k]]