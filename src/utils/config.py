"""
Configuration management for Voice RAG Assistant (Hybrid RAG)
"""
import os
from dataclasses import dataclass
from typing import Dict, Any
import os

# CRITICAL FIX: Prevent PyTorch/OpenMP crashes on macOS
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

# Disable tokenizers parallelism to prevent fork warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ... rest of your imports and classes ...
# Disable tokenizers parallelism to prevent fork warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

@dataclass
class ModelConfig:
    """Model configuration"""
    gpt4all_model_name: str = "Llama-3.2-1B-Instruct-Q4_0.gguf"
    embedding_model_name: str = "all-MiniLM-L6-v2"
    clip_model_name: str = "openai/clip-vit-base-patch32"
    # Changed from 'base' to 'tiny.en' for standard transformers implementation
    whisper_model_size: str = "tiny.en" 

@dataclass
class AudioConfig:
    """Audio processing configuration"""
    sample_rate: int = 16000
    chunk_size: int = 1024
    channels: int = 1
    record_duration: int = 5
    silence_threshold: float = 0.01
    # Adjusted rate for Coqui/Piper (1.25x speed)
    tts_rate: int = 125 
    tts_volume: float = 0.8
    # Changed from 'auto' to 'hybrid' for Coqui/Piper
    tts_engine: str = "hybrid" 
    
    # Voice activity detection
    vad_enabled: bool = True
    vad_aggressiveness: int = 3
    
    # Audio enhancement
    noise_reduction: bool = True
    auto_gain_control: bool = True
    
    # Multi-language support
    whisper_language: str = "auto"
    tts_language: str = "en"

@dataclass
class RAGConfig:
    """RAG system configuration (Modified for FAISS/SQLite)"""
    
    image_db_path: str = "./knowledge_base.db" 
    image_dir: str = "./data/images"
    
    # Text processing
    max_words_per_chunk: int = 200
    overlap_words: int = 50
    
    # Image processing
    min_image_size: int = 80
    max_images_returned: int = 3 # Reduced slightly to save space
    page_context_window: int = 2
    
    # == UPDATED THRESHOLDS (Lowered to ensure images appear) ==
    clip_similarity_threshold: float = 0.12  # Was 0.15
    context_similarity_threshold: float = 0.20 # Was 0.25
    combined_score_threshold: float = 0.25   # Was 0.3
    
    # Scoring weights
    clip_weight: float = 0.5
    context_weight: float = 0.3
    proximity_weight: float = 0.2
    
@dataclass
class SystemConfig:
    """System configuration"""
    pdf_dir: str = "./data/pdfs"
    models_dir: str = "./models"
    max_tokens: int = 512
    temperature: float = 0.7
    debug: bool = False
    
    # Performance settings
    max_concurrent_requests: int = 4
    cache_enabled: bool = True
    cache_size: int = 100
    
    # UI settings
    theme: str = "auto"
    show_technical_details: bool = False
    auto_scroll_chat: bool = True
    
    # Security settings
    safe_mode: bool = True
    content_filter: bool = True

class Config:
    """Main configuration class"""
    def __init__(self):
        self.models = ModelConfig()
        self.audio = AudioConfig()
        self.rag = RAGConfig()
        self.system = SystemConfig()
        
        self._load_from_env()
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        if os.getenv('GPT4ALL_MODEL_NAME'):
            self.models.gpt4all_model_name = os.getenv('GPT4ALL_MODEL_NAME')
        
        # Removed vector_db_dir check here
            
        if os.getenv('PDF_DIR'):
            self.system.pdf_dir = os.getenv('PDF_DIR')
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the LLM"""
        return """You are a strict AI exam tutor. Your knowledge is limited EXCLUSIVELY to the provided context materials.

**Strict Instructions:**
1.  **Source of Truth:** Answer the user's question using *only* the information found in the Context provided below. Do NOT use your internal knowledge base, even for common facts.
2.  **No Hallucinations:** If the answer is not explicitly stated in the Context, you must reply: "I don't know. I couldn't find relevant information in the provided documents." Do not attempt to guess or fill in gaps.
3.  **Corrections:** If the provided Context contains a clear factual error, answer based on the text but list numbered corrections at the end and append "(corrected)".
4.  **Conciseness:** Keep responses precise and exam-focused. Remove conversational filler.

**Context:**
"""

# Global configuration instance
config = Config()