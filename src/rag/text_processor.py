"""
Text processing functionality for RAG system (Modified for Hybrid RAG)
"""
import os
import re
import uuid
import json
from typing import List, Dict, Any, Tuple
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
from collections import Counter
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk.corpus import stopwords
from .vector_db import VectorDatabase
from ..utils.config import config

class TextProcessor:
    """Text processing and indexing"""
    
    def __init__(self, vector_db: VectorDatabase):
        self.vector_db = vector_db
        self.embedder = None
        self._initialize_embedder()
    
    def _initialize_embedder(self):
        """Initialize text embedder"""
        try:
            print("[INFO] Loading text embedder...")
            self.embedder = SentenceTransformer(config.models.embedding_model_name)
            print("[INFO] Text embedder loaded successfully")
        except Exception as e:
            print(f"[ERROR] Failed to load text embedder: {e}")
            raise
    
    def extract_pdf_text_by_pages(self, pdf_path: str) -> List[Tuple[int, str]]:
        """Extract text from PDF page by page"""
        try:
            reader = PdfReader(pdf_path)
            pages = []
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    pages.append((page_num, page_text))
            return pages
        except Exception as e:
            print(f"[ERROR] Failed to extract text from {pdf_path}: {e}")
            return []
    
    def chunk_text(self, text: str, max_words: int = None, overlap_words: int = None) -> List[str]:
        """
        Chunk text into smaller pieces.
      
        """
        if max_words is None:
            max_words = config.rag.max_words_per_chunk
        if overlap_words is None:
            overlap_words = config.rag.overlap_words
        
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_word_count = 0
        
        for sentence in sentences:
            sentence_words = sentence.split()
            sentence_word_count = len(sentence_words)
            
            if current_word_count + sentence_word_count > max_words and current_chunk:
                chunks.append(" ".join(current_chunk))
                
                if overlap_words > 0:
                    overlap_text = " ".join(current_chunk[-overlap_words:])
                    current_chunk = [overlap_text, sentence]
                    current_word_count = len(overlap_text.split()) + sentence_word_count
                else:
                    current_chunk = [sentence]
                    current_word_count = sentence_word_count
            else:
                current_chunk.append(sentence)
                current_word_count += sentence_word_count
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def _extract_enhanced_tags(self, text: str) -> List[str]:
        """
        Extract meaningful tags from text using NLTK (Noun extraction + Pattern matching)
        """
        try:
            # 1. Scientific pattern matching
            scientific_patterns = [
                r'\b[A-Z][a-z]+(?:ose|ase|ine|ate|ide)\b', # chemicals
                r'\b(?:test|experiment|activity|method|procedure)\b', # processes
                r'\b(?:starch|protein|carbohydrate|fat|glucose|enzyme)\b', # biology
            ]
            pattern_tags = []
            for pattern in scientific_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                pattern_tags.extend([m.lower() for m in matches])

            # 2. Noun extraction
            tokens = word_tokenize(text.lower())
            tagged = pos_tag(tokens)
            nouns = [word for word, tag in tagged if tag in ['NN', 'NNS', 'NNP', 'NNPS']]
            
            all_tags = pattern_tags + nouns 
            stop_words = set(stopwords.words('english'))
            
            # 3. Filtering
            filtered_tags = [
                tag for tag in all_tags
                if tag not in stop_words
                and len(tag) > 2
                and tag not in ['image', 'content', 'figure', 'table', 'page', 'text', 'section']
            ]

            # Return top 5 most frequent tags
            tag_counts = Counter(filtered_tags)
            return [tag for tag, _ in tag_counts.most_common(5)]
            
        except Exception as e:
            # Fallback if NLTK fails
            return []
    
    def process_pdfs_directory(self, pdf_dir: str = None) -> Dict[str, Any]:
        """Process all PDFs in a directory and return all paragraphs for indexing"""
        if pdf_dir is None: pdf_dir = config.system.pdf_dir
        
        if not os.path.exists(pdf_dir):
            return {"success": False, "error": "Directory not found", "all_paragraphs": []}
        
        pdf_files = [os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            return {"success": False, "error": "No PDF files found", "all_paragraphs": []}
        
        all_paragraphs = []
        successful_pdfs = 0
        
        for pdf_path in pdf_files:
            pdf_name = os.path.basename(pdf_path)
            print(f"[INFO] Processing text: {pdf_name}")
            
            try:
                pages = self.extract_pdf_text_by_pages(pdf_path)
                
                for page_num, page_text in pages:
                    chunks = self.chunk_text(page_text)
                    
                    for i, chunk in enumerate(chunks):
                        chunk_id = str(uuid.uuid4())
                        tags = self._extract_enhanced_tags(chunk)
                        
                        paragraph_data = {
                            "id": chunk_id,
                            "text": chunk,
                            "header": f"Section {i+1}", 
                            "page_num": page_num,
                            "source_pdf": pdf_name,
                            "bbox_range": "[]", # Text-only processing doesn't get bboxes easily
                            "tags": tags,
                            "full_page_ocr": page_text
                        }
                        
                        # Store in SQLite immediately
                        self.vector_db.add_paragraph_metadata(paragraph_data)
                        
                        # Add to list for FAISS indexing later
                        all_paragraphs.append(paragraph_data)
                
                successful_pdfs += 1
                
            except Exception as e:
                print(f"[ERROR] Failed to process {pdf_name}: {e}")

        total_chunks = len(all_paragraphs)
        print(f"[INFO] Text processing complete: {successful_pdfs}/{len(pdf_files)} PDFs, {total_chunks} chunks")
        
        return {
            "success": successful_pdfs > 0,
            "total_chunks": total_chunks,
            "all_paragraphs": all_paragraphs # Returned to main.py for FAISS indexing
        }
    
    def get_embedder(self) -> SentenceTransformer:
        return self.embedder