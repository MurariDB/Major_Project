import os
import shutil
from sentence_transformers import SentenceTransformer
from transformers import CLIPProcessor, CLIPModel, WhisperProcessor, WhisperForConditionalGeneration

# Define local paths
MODEL_DIR = "./models"
TEXT_PATH = os.path.join(MODEL_DIR, "text_embedder")
CLIP_PATH = os.path.join(MODEL_DIR, "clip")
WHISPER_PATH = os.path.join(MODEL_DIR, "whisper")

os.makedirs(MODEL_DIR, exist_ok=True)

def download_and_save():
    print("🚀 Starting Offline Model Download...")
    print("   (This may take a few minutes depending on your internet speed)")

    # 1. Text Embedder (The one causing your error)
    print(f"\n[1/3] Downloading Sentence Transformer to {TEXT_PATH}...")
    if not os.path.exists(TEXT_PATH):
        model = SentenceTransformer('all-MiniLM-L6-v2')
        model.save(TEXT_PATH)
        print("   ✅ Text Embedder Saved.")
    else:
        print("   ⚠️ Text Embedder already exists. Skipping.")

    # 2. CLIP Model (For Images)
    print(f"\n[2/3] Downloading CLIP to {CLIP_PATH}...")
    if not os.path.exists(CLIP_PATH):
        clip_model_name = "openai/clip-vit-base-patch32"
        processor = CLIPProcessor.from_pretrained(clip_model_name)
        model = CLIPModel.from_pretrained(clip_model_name)
        
        processor.save_pretrained(CLIP_PATH)
        model.save_pretrained(CLIP_PATH)
        print("   ✅ CLIP Saved.")
    else:
        print("   ⚠️ CLIP already exists. Skipping.")

    # 3. Whisper Model (For Voice)
    print(f"\n[3/3] Downloading Whisper to {WHISPER_PATH}...")
    if not os.path.exists(WHISPER_PATH):
        whisper_name = "openai/whisper-tiny.en"
        processor = WhisperProcessor.from_pretrained(whisper_name)
        model = WhisperForConditionalGeneration.from_pretrained(whisper_name)
        
        processor.save_pretrained(WHISPER_PATH)
        model.save_pretrained(WHISPER_PATH)
        print("   ✅ Whisper Saved.")
    else:
        print("   ⚠️ Whisper already exists. Skipping.")

    print("\n🎉 All models downloaded! You can now go OFFLINE.")

if __name__ == "__main__":
    download_and_save()