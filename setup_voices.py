import os
import shutil
from huggingface_hub import hf_hub_download

def setup_piper_voice():
    # Target folder
    voice_dir = os.path.join("piper_voices", "en_US")
    if os.path.exists(voice_dir): shutil.rmtree(voice_dir)
    os.makedirs(voice_dir, exist_ok=True)
    
    print(f"⬇️  Downloading Voice Model to {voice_dir}...")
    
    repo = "rhasspy/piper-voices"
    # Using 'lessac' (high quality, stable)
    onnx_file = "en/en_US/lessac/medium/en_US-lessac-medium.onnx"
    json_file = "en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
    
    # Download
    onnx_path = hf_hub_download(repo_id=repo, filename=onnx_file, local_dir=voice_dir)
    json_path = hf_hub_download(repo_id=repo, filename=json_file, local_dir=voice_dir)
    
    # Rename to standard 'voice.onnx' / 'voice.json'
    shutil.move(onnx_path, os.path.join(voice_dir, "voice.onnx"))
    shutil.move(json_path, os.path.join(voice_dir, "voice.json"))
    
    # Cleanup cache artifacts
    for item in os.listdir(voice_dir):
        if item.startswith("."): shutil.rmtree(os.path.join(voice_dir, item), ignore_errors=True)

    print("✅ Voice setup complete.")

if __name__ == "__main__":
    setup_piper_voice()
