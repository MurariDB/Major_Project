"""
Simplified Speech-to-Text using Whisper (Edge/Offline Ready)
"""
import sounddevice as sd
import numpy as np
import torch
import time
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from ..utils.config import config

class SpeechToText:
    """Simple Speech-to-Text processor"""
    
    def __init__(self):
        self.processor = None
        self.model = None
        self.is_recording = False
        self.frames = [] # Store audio chunks here
        self.sample_rate = 16000
        
        # Check for GPU
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def _load_model(self):
        """Lazy load the model only when needed"""
        if self.model is not None:
            return
            
        print(f"[INFO] Loading Whisper model on {self.device}...")
        try:
            # Use the path defined in config (e.g., "./models/whisper" or "openai/whisper-tiny.en")
            model_path = getattr(config.models, "whisper_model_path", "openai/whisper-tiny.en")
            
            self.processor = WhisperProcessor.from_pretrained(model_path)
            self.model = WhisperForConditionalGeneration.from_pretrained(model_path).to(self.device)
            print("[INFO] Whisper loaded!")
        except Exception as e:
            print(f"[ERROR] Could not load Whisper: {e}")

    def _callback(self, indata, frames, time, status):
        """Simple audio collection callback"""
        if self.is_recording:
            self.frames.append(indata.copy())

    def start_recording(self):
        """Start capturing audio"""
        self.frames = []
        self.is_recording = True
        
        # Start non-blocking stream
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            callback=self._callback
        )
        self.stream.start()
        print("[INFO] Recording started...")

    def stop_recording(self):
        """Stop capturing"""
        self.is_recording = False
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        print(f"[INFO] Recording stopped. Captured {len(self.frames)} chunks.")

    def transcribe(self):
        """Convert captured audio to text"""
        self._load_model()
        
        if not self.frames:
            return ""
            
        # 1. Flatten audio chunks into one long array
        audio = np.concatenate(self.frames, axis=0).flatten()
        
        # 2. Transcribe
        print("[INFO] Transcribing...")
        input_features = self.processor(
            audio, 
            sampling_rate=self.sample_rate, 
            return_tensors="pt"
        ).input_features.to(self.device)
        
        predicted_ids = self.model.generate(input_features)
        transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        
        print(f"[RESULT] You said: {transcription}")
        return transcription.strip()

    def record_and_transcribe(self, duration=5):
        """
        Hybrid helper: 
        1. If audio was manually recorded (via UI start/stop), transcribe that.
        2. If no audio, record for fixed 'duration' seconds.
        """
        # If we already have data from manual start/stop, use it
        if self.frames and not self.is_recording:
            return self.transcribe()
            
        # Otherwise, do a blocking record (CLI mode)
        self.start_recording()
        time.sleep(duration)
        self.stop_recording()
        return self.transcribe()