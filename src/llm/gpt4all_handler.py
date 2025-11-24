"""
GPT4All LLM handler for local inference
"""
import os
from typing import Optional, Dict, Any, List
from gpt4all import GPT4All
from ..utils.config import config

class GPT4AllHandler:
    """Handler for GPT4All local LLM"""
    
    def __init__(self):
        self.model = None
        self.model_name = config.models.gpt4all_model_name
        self.max_tokens = config.system.max_tokens
        self.temperature = config.system.temperature
        
        # Initialize model
        #self._initialize_model()
    
    def _ensure_model_loaded(self):
        if self.model is None:
            try:
                print(f"[INFO] Lazy loading GPT4All model: {self.model_name}")
                self.model = GPT4All(self.model_name)
                print("[INFO] GPT4All model loaded successfully")
            except Exception as e:
                print(f"[ERROR] Failed to load GPT4All model: {e}")
                raise

    def _initialize_model(self):
        """Initialize GPT4All model"""
        try:
            print(f"[INFO] Loading GPT4All model: {self.model_name}")
            self.model = GPT4All(self.model_name)
            print("[INFO] GPT4All model loaded successfully")
        except Exception as e:
            print(f"[ERROR] Failed to load GPT4All model: {e}")
            raise
    
    def generate_response(self, prompt: str, max_tokens: int = None, 
                         temperature: float = None, streaming: bool = False) -> str:
        """Generate response from the model"""
        self._ensure_model_loaded()
        if self.model is None:
            raise RuntimeError("Model not initialized")
        
        # Use default values if not provided
        if max_tokens is None:
            max_tokens = self.max_tokens
        if temperature is None:
            temperature = self.temperature
        
        try:
            if streaming:
                return self._generate_streaming(prompt, max_tokens, temperature)
            else:
                return self._generate_non_streaming(prompt, max_tokens, temperature)
                
        except Exception as e:
            print(f"[ERROR] Generation failed: {e}")
            return "I apologize, but I encountered an error while processing your request."
    
    def _generate_non_streaming(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate response without streaming"""
        with self.model.chat_session():
            response = self.model.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temp=temperature
            )
            return response.strip()
    
    def _generate_streaming(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate response with streaming (for real-time display)"""
        full_response = ""
        
        with self.model.chat_session():
            for token in self.model.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temp=temperature,
                streaming=True
            ):
                full_response += token
                print(token, end="", flush=True)
        
        return full_response.strip()
    
    def chat_with_context(self, query: str, context: List[str], 
                         system_prompt: str = None) -> str:
        """Generate response with RAG context"""
        self._ensure_model_loaded()
        if system_prompt is None:
            system_prompt = config.get_system_prompt()
        
        # Build the complete prompt
        prompt = system_prompt + "\n\n### Context ###\n"
        
        for i, ctx in enumerate(context, 1):
            prompt += f"**Context {i}:**\n{ctx}\n\n"
        
        prompt += f"### Question ###\n{query}\n\n### Answer ###\n"
        
        return self.generate_response(prompt)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_name": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "is_loaded": self.model is not None
        }
    
    def reload_model(self):
        """Reload the model"""
        self._initialize_model()