"""
Text-to-Speech functionality using Piper TTS (Source Build Version)
"""
import os
import sys
import subprocess
import threading
import queue
import tempfile
from typing import Optional
from ..utils.config import config

# --- PATH CONFIGURATION (Matching app.py) ---
BASE_DIR = os.getcwd()
PIPER_DIR = os.path.join(BASE_DIR, "piper")

# 1. Executable Path (Source Build Structure)
PIPER_EXECUTABLE = os.path.join(PIPER_DIR, "build", "piper")

# 2. Data Path
# app.py uses the Homebrew path. We'll check for a local one first, then fall back.
LOCAL_ESPEAK = os.path.join(PIPER_DIR, "espeak-ng-data")
SYSTEM_ESPEAK = "/opt/homebrew/share/espeak-ng-data"
ESPEAK_DATA = LOCAL_ESPEAK if os.path.exists(LOCAL_ESPEAK) else SYSTEM_ESPEAK

# 3. Voice Models
VOICE_DIR = os.path.join(BASE_DIR, "piper_voices", "en_US")
PIPER_MODEL_PATH = os.path.join(VOICE_DIR, "voice.onnx")
PIPER_CONFIG_PATH = os.path.join(VOICE_DIR, "voice.json")

class TextToSpeech:
    def __init__(self):
        self.is_speaking = False
        self.speech_queue = queue.Queue()
        self.speech_thread = None
        self.stop_event = threading.Event()
        self._check_setup()
        self._start_speech_thread()
    
    def _check_setup(self):
        print(f"\n🔍 Checking Piper Configuration...")
        print(f"   - Executable: {PIPER_EXECUTABLE}")
        print(f"   - Data: {ESPEAK_DATA}")
        
        if not os.path.exists(PIPER_EXECUTABLE):
            print(f"❌ Executable missing! (Check {PIPER_EXECUTABLE})")
        if not os.path.exists(ESPEAK_DATA):
            print(f"❌ Data missing! (Check {ESPEAK_DATA})")

    def _start_speech_thread(self):
        self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.speech_thread.start()
    
    def _speech_worker(self):
        while not self.stop_event.is_set():
            try:
                text = self.speech_queue.get(timeout=1)
                if text is None: break
                self.is_speaking = True
                self._speak_text(text)
                self.is_speaking = False
                self.speech_queue.task_done()
            except queue.Empty: continue
            except Exception as e: print(f"[ERROR] Worker: {e}")

    def _speak_text(self, text: str):
        if not os.path.exists(PIPER_EXECUTABLE): return

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                output_path = tmp.name

            length_scale = str(1.0 / (config.audio.tts_rate / 100.0))
            
            command = [
                PIPER_EXECUTABLE,
                "--model", PIPER_MODEL_PATH,
                "--config", PIPER_CONFIG_PATH,
                "--output_file", output_path,
                "--length_scale", length_scale,
                "--espeak_data", ESPEAK_DATA
            ]
            
            # Inject DYLD_LIBRARY_PATH for macOS dynamic libraries
            # This points to the 'build' folder where libs usually sit in a source build
            lib_path = os.path.dirname(PIPER_EXECUTABLE)
            my_env = os.environ.copy()
            my_env["DYLD_LIBRARY_PATH"] = f"{lib_path}:{my_env.get('DYLD_LIBRARY_PATH', '')}"

            subprocess.run(
                command, 
                input=text, 
                encoding='utf-8', 
                check=True, 
                capture_output=True,
                env=my_env
            )
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                self._play_audio(output_path)
                try: os.remove(output_path)
                except: pass
            else:
                print("[WARN] Empty audio file generated")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Piper Error: {e.stderr}")
        except Exception as e:
            print(f"❌ System Error: {e}")

    def _play_audio(self, file_path):
        os.system(f"afplay '{file_path}'")

    def speak(self, text: str, blocking: bool = False):
        if blocking:
            self.is_speaking = True
            self._speak_text(text)
            self.is_speaking = False
        else:
            self.speech_queue.put(text)
            
    def cleanup(self):
        self.stop_event.set()
        if self.speech_thread and self.speech_thread.is_alive():
            try: self.speech_queue.put(None); self.speech_thread.join(timeout=2)
            except: pass