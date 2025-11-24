"""
Speech-to-Text functionality using standard Whisper (Transformers)
"""
import numpy as np
import sounddevice as sd
import threading
import queue
import time
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from typing import Optional, Callable
from ..utils.config import config

# Try to import webrtcvad for voice activity detection
try:
    import webrtcvad
    VAD_AVAILABLE = True
except ImportError:
    VAD_AVAILABLE = False
    print("[WARN] webrtcvad not available. Install with: pip install webrtcvad")

# Try to import librosa for audio enhancement
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("[WARN] librosa not available. Install with: pip install librosa")

class SpeechToText:
    """Real-time speech-to-text processor"""
    
    def __init__(self):
        self.processor = None
        self.model = None
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.sample_rate = config.audio.sample_rate
        self.chunk_size = config.audio.chunk_size
        self.channels = config.audio.channels
        
        # Voice Activity Detection
        self.vad = None
        if VAD_AVAILABLE and config.audio.vad_enabled:
            self.vad = webrtcvad.Vad(config.audio.vad_aggressiveness)
        
        # Initialize Whisper model
        #self._initialize_model()
    
    def _ensure_model_loaded(self):
        if self.model is None:
            try:
                print("[INFO] Lazy loading Whisper model...")
                model_id = "openai/whisper-tiny.en"
                self.processor = WhisperProcessor.from_pretrained(model_id)
                self.model = WhisperForConditionalGeneration.from_pretrained(model_id)
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self.model = self.model.to(device)
                print(f"[INFO] Whisper model loaded successfully on {device}")
            except Exception as e:
                print(f"[ERROR] Failed to load Whisper model: {e}")
                raise

    def _initialize_model(self):
        """Initialize the Whisper model (using transformers)"""
        try:
            print("[INFO] Loading Whisper model...")
            model_id = "openai/whisper-tiny.en"
            self.processor = WhisperProcessor.from_pretrained(model_id)
            self.model = WhisperForConditionalGeneration.from_pretrained(model_id)
            
            # Use CPU by default for compatibility, or CUDA if confident
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = self.model.to(device)
            
            print(f"[INFO] Whisper model loaded successfully on {device}")
        except Exception as e:
            print(f"[ERROR] Failed to load Whisper model: {e}")
            raise
    
    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio input"""
        if status:
            print(f"[WARN] Audio callback status: {status}")
        
        if self.is_recording:
            # Convert to mono if stereo
            if indata.shape[1] > 1:
                audio_data = np.mean(indata, axis=1)
            else:
                audio_data = indata.flatten()
            
            self.audio_queue.put(audio_data.copy())
    
    def start_recording(self):
        """Start recording audio"""
        self.is_recording = True
        self.audio_queue.queue.clear()
        
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=self._audio_callback,
                blocksize=self.chunk_size,
                dtype=np.float32
            )
            self.stream.start()
            print("[INFO] Recording started...")
        except Exception as e:
            print(f"[ERROR] Failed to start recording: {e}")
            self.is_recording = False
            raise
    
    def stop_recording(self):
        """Stop recording audio"""
        self.is_recording = False
        
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        
        print("[INFO] Recording stopped")
    
    def get_audio_data(self, duration: int = 5) -> np.ndarray:
        """Get audio data for specified duration"""
        audio_data = []
        samples_needed = int(self.sample_rate * duration)
        samples_collected = 0
        
        start_time = time.time()
        timeout = duration + 2  # 2 second timeout buffer
        
        while samples_collected < samples_needed:
            if time.time() - start_time > timeout:
                print("[WARN] Audio collection timeout")
                break
            
            try:
                chunk = self.audio_queue.get(timeout=0.1)
                audio_data.append(chunk)
                samples_collected += len(chunk)
            except queue.Empty:
                continue
        
        if not audio_data:
            return np.array([])
        
        # Concatenate and trim to exact duration
        audio_array = np.concatenate(audio_data)
        return audio_array[:samples_needed]
    
    def transcribe_audio(self, audio_data: np.ndarray) -> str:
        """Transcribe audio data to text with enhanced processing"""
        self._ensure_model_loaded() # <--- ADD THIS
        if self.model is None or self.processor is None:
            raise RuntimeError("Whisper model not initialized")

        if len(audio_data) == 0:
            return ""

        # Check for voice activity first
        if not self._detect_voice_activity(audio_data):
            print("[INFO] No voice activity detected")
            return ""

        # Enhance audio quality
        enhanced_audio = self._enhance_audio(audio_data)

        # Check for silence after enhancement
        if np.max(np.abs(enhanced_audio)) < config.audio.silence_threshold:
            return ""

        try:
            print("[INFO] Transcribing audio...")
            
            # Prepare audio features
            input_features = self.processor(
                enhanced_audio, 
                sampling_rate=self.sample_rate, 
                return_tensors="pt"
            ).input_features.to(self.model.device)
            
            # Generate predicted IDs
            predicted_ids = self.model.generate(input_features)
            
            # Decode transcription
            transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]

            text = transcription.strip()
            if text:
                print(f"[INFO] Transcription: {text}")

            return text

        except Exception as e:
            print(f"[ERROR] Transcription failed: {e}")
            return ""
    
    def record_and_transcribe(self, duration: int = 5) -> str:
        """Record audio and transcribe it"""
        self.start_recording()
        try:
            audio_data = self.get_audio_data(duration)
            return self.transcribe_audio(audio_data)
        finally:
            self.stop_recording()
    
    def get_available_devices(self):
        """Get available audio input devices"""
        devices = sd.query_devices()
        input_devices = []
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                input_devices.append({
                    'index': i,
                    'name': device['name'],
                    'channels': device['max_input_channels'],
                    'sample_rate': device['default_samplerate']
                })
        return input_devices
    
    def _enhance_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """Enhance audio quality using various techniques"""
        if len(audio_data) == 0:
            return audio_data
        
        enhanced_audio = audio_data.copy()
        
        # Noise reduction using spectral subtraction (if librosa available)
        if LIBROSA_AVAILABLE and config.audio.noise_reduction:
            try:
                stft = librosa.stft(enhanced_audio)
                magnitude = np.abs(stft)
                phase = np.angle(stft)
                noise_floor = np.mean(magnitude[:, :10], axis=1, keepdims=True)
                clean_magnitude = magnitude - 0.5 * noise_floor
                clean_magnitude = np.maximum(clean_magnitude, 0.1 * magnitude)
                clean_stft = clean_magnitude * np.exp(1j * phase)
                enhanced_audio = librosa.istft(clean_stft)
            except Exception as e:
                print(f"[WARN] Noise reduction failed: {e}")
        
        # Auto gain control
        if config.audio.auto_gain_control:
            max_val = np.max(np.abs(enhanced_audio))
            if max_val > 0:
                target_level = 0.5
                gain = target_level / max_val
                enhanced_audio = enhanced_audio * gain
        
        return enhanced_audio
    
    def _detect_voice_activity(self, audio_chunk: np.ndarray) -> bool:
        """Detect if audio chunk contains voice activity"""
        if not self.vad or len(audio_chunk) == 0:
            return True  # Assume voice activity if VAD not available
        
        try:
            # Convert to 16-bit PCM for VAD
            audio_int16 = (audio_chunk * 32767).astype(np.int16)
            frame_duration = 30  # ms
            frame_size = int(self.sample_rate * frame_duration / 1000)
            
            voice_frames = 0
            total_frames = 0
            
            for i in range(0, len(audio_int16) - frame_size, frame_size):
                frame = audio_int16[i:i + frame_size].tobytes()
                if self.vad.is_speech(frame, self.sample_rate):
                    voice_frames += 1
                total_frames += 1
            
            return total_frames == 0 or (voice_frames / total_frames) > 0.3
            
        except Exception as e:
            # print(f"[WARN] VAD failed: {e}")
            return True