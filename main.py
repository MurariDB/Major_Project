"""
Main application for Voice RAG Assistant - Enhanced Edition (Hybrid RAG)
"""
import os
import sys
import time
import threading
import numpy as np
import json
import faiss 
import nltk 
from typing import Optional, List, Dict, Any

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.audio.speech_to_text import SpeechToText
from src.audio.text_to_speech import TextToSpeech
from src.rag.vector_db import VectorDatabase
from src.rag.text_processor import TextProcessor
from src.rag.image_processor import ImageProcessor
from src.rag.retrieval import RetrievalSystem
from src.llm.gpt4all_handler import GPT4AllHandler
from src.utils.config import config
from src.utils.performance_monitor import performance_monitor

class VoiceRAGAssistant:
    """Main Voice RAG Assistant application (Hybrid Architecture)"""
    
    def __init__(self):
        self.stt = None
        self.tts = None
        self.vector_db = None
        self.text_processor = None
        self.image_processor = None
        self.retrieval_system = None
        self.llm = None
        self.is_initialized = False
        
        # Start performance monitoring
        performance_monitor.start_monitoring()
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all components with dependency checks"""
        try:
            print("🚀 Initializing Voice RAG Assistant (Hybrid RAG)...")
            
            # 0. NLTK Setup
            print("[0/7] Verifying NLTK data...")
            try:
                nltk.data.find('tokenizers/punkt')
                nltk.data.find('taggers/averaged_perceptron_tagger')
                nltk.data.find('corpora/stopwords')
            except LookupError:
                print("    - Downloading missing NLTK datasets...")
                nltk.download('punkt', quiet=True)
                nltk.download('averaged_perceptron_tagger', quiet=True)
                nltk.download('stopwords', quiet=True)
            
            # 1. Initialize vector database
            print("[1/7] Initializing vector database...")
            self.vector_db = VectorDatabase()
            
            # 2. Initialize text processor
            print("[2/7] Initializing text processor...")
            self.text_processor = TextProcessor(self.vector_db)
            
            # 3. Initialize image processor (CLIP + OpenCV)
            print("[3/7] Initializing image processor...")
            self.image_processor = ImageProcessor(self.vector_db)
            
            # 4. Initialize retrieval system
            print("[4/7] Initializing retrieval system...")
            self.retrieval_system = RetrievalSystem(self.vector_db)
            
            # 5. Initialize LLM
            print("[5/7] Initializing LLM...")
            self.llm = GPT4AllHandler()
            
            # 6. Initialize Audio
            print("[6/7] Initializing Audio Systems...")
            self.stt = SpeechToText()
            self.tts = TextToSpeech()
            
            self.is_initialized = True
            print("✅ All components initialized successfully!")
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            raise

    def ingest_documents(self, pdf_dir: str = None) -> Dict[str, Any]:
        """Ingest PDFs with full pipeline"""
        if not self.is_initialized:
            raise RuntimeError("Assistant not initialized")
        
        if pdf_dir is None:
            pdf_dir = config.system.pdf_dir

        print(f"\n📚 Starting hybrid document ingestion from: {pdf_dir}")
        start_time = time.time()
        
        # --- Step 1: Text ---
        print("   Processing text content (Extraction + Tagging)...")
        text_result = self.text_processor.process_pdfs_directory(pdf_dir)
        all_paragraphs = text_result.get("all_paragraphs", [])
        
        # --- Step 2: Images ---
        print("   Processing images (Detection + CLIP + Base64 Storage)...")
        image_result = self.image_processor.process_pdfs_directory(
            pdf_dir, 
            self.text_processor.get_embedder()
        )
        
        # --- Step 3: FAISS Index ---
        if all_paragraphs:
            print(f"   Building FAISS index for {len(all_paragraphs)} text chunks...")
            texts = [p['text'] for p in all_paragraphs]
            
            embeddings = self.text_processor.get_embedder().encode(
                texts, 
                normalize_embeddings=True, 
                convert_to_tensor=False
            ).astype('float32')
            
            success = self.vector_db.save_text_faiss_index(embeddings, all_paragraphs)
            self.vector_db.save_bm25_index(all_paragraphs)
            if not success:
                print("❌ Failed to save FAISS index.")
        else:
            print("⚠️ No text paragraphs found to index.")
        
        duration = time.time() - start_time
        result = {
            "success": text_result["success"] or image_result["success"],
            "text_chunks": len(all_paragraphs),
            "images_indexed": image_result.get("total_indexed", 0),
            "duration": duration
        }
        
        print(f"📊 Ingestion Complete ({duration:.2f}s):")
        print(f"   - Text Chunks: {result['text_chunks']}")
        print(f"   - Images Indexed: {result['images_indexed']}")
        print(f"   - SQLite Text Count: {self.vector_db.get_text_collection_count()}")
        
        return result
    
    def process_voice_query(self, duration: int = 5) -> Dict[str, Any]:
        """Process voice query"""
        if not self.is_initialized:
            raise RuntimeError("Assistant not initialized")
        
        print("\n🎤 Listening for voice input...")
        
        user_text = self.stt.record_and_transcribe(duration)
        
        if not user_text or not user_text.strip():
            return {
                "success": False,
                "error": "No speech detected",
                "query": "",
                "response": "",
                "images": []
            }
        
        print(f"🗣️ You said: {user_text}")
        return self.process_text_query(user_text, speak_response=True)

    def process_text_query(self, query: str, speak_response: bool = False) -> Dict[str, Any]:
        """Process text query with Hybrid RAG"""
        if not self.is_initialized:
            raise RuntimeError("Assistant not initialized")

        print(f"\n💭 Processing query: {query}")
        start_time = time.time()

        try:
            # --- CRITICAL FIX: Load CLIP properly before using it ---
            """clip_model, clip_processor = self.image_processor.get_clip_model()
            
            # 1. & 2. Hybrid Retrieval
            text_docs, text_metas, image_paths = self.retrieval_system.retrieve_multimodal(
                query=query,
                text_embedder=self.text_processor.get_embedder(),
                clip_model=clip_model,           # Pass actual loaded model
                clip_processor=clip_processor    # Pass actual loaded processor
            )"""
            # Hybrid Retrieval (no CLIP needed now)
            text_docs, text_metas, image_paths = self.retrieval_system.retrieve_multimodal(
                query=query,
                text_embedder=self.text_processor.get_embedder(),
                clip_model=None,  # Not used anymore
                clip_processor=None ,
                 text_top_k=3 # Not used anymore
            )

            # 3. Generate Response
            if text_docs or image_paths:
                response = self.llm.chat_with_context(
                    query=query,
                    context=text_docs
                )
            else:
                response = "I couldn't find relevant information in the provided documents."

            print(f"🤖 Response: {response}")
            
            # 4. TTS Output
            if speak_response and response:
                print("🔊 Speaking response...")
                self.tts.speak(response)

            if image_paths:
                print(f"🖼️ Found {len(image_paths)} relevant images")

            processing_time = time.time() - start_time
            performance_monitor.record_response_time(start_time)

            return {
                "success": True,
                "query": query,
                "response": response,
                "images": image_paths,
                "contexts": text_docs,
                "text_sources": len(text_docs),
                "processing_time": processing_time
            }

        except Exception as e:
            print(f"❌ Query processing failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "response": "I encountered an error while processing your request.",
                "images": [],
                "processing_time": time.time() - start_time
            }
    
    def run_cli_mode(self):
        """Run in CLI mode"""
        print("\n🟢 Voice RAG Assistant CLI Mode")
        print("Commands: 'voice', 'text', 'ingest', 'status', 'exit'")
        
        while True:
            try:
                user_input = input("\nCommand: ").strip().lower()
                
                if user_input in ['exit', 'quit', 'q']:
                    self.cleanup()
                    break
                
                elif user_input in ['voice', 'v']:
                    self.process_voice_query()
                
                elif user_input in ['text', 't']:
                    q = input("Question: ")
                    if q: self.process_text_query(q)
                
                elif user_input in ['ingest', 'i']:
                    self.ingest_documents()
                    
                elif user_input in ['status', 's']:
                    self.show_status()
                    
            except KeyboardInterrupt:
                self.cleanup()
                break
    
    def show_status(self):
        print("\n📊 System Status:")
        print(f"   - DB Text Count: {self.vector_db.get_text_collection_count()}")
        print(f"   - DB Image Count: {self.vector_db.get_image_collection_count()}")
        metrics = performance_monitor.get_current_metrics()
        if metrics:
            print(f"   - Memory Usage: {metrics.memory_usage_mb:.1f} MB")
    
    def cleanup(self):
        print("\n🧹 Cleaning up...")
        performance_monitor.stop_monitoring()
        if self.tts: self.tts.cleanup()
        if self.stt: 
            try: self.stt.stop_recording()
            except: pass
        if self.vector_db: self.vector_db.close()
        print("✅ Cleanup completed")

if __name__ == "__main__":
    app = VoiceRAGAssistant()
    app.run_cli_mode()