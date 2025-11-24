# debug_piper.py
import os

# Define paths exactly as the app sees them
PIPER_EXEC = "./piper/build/piper"
VOICE_MODEL = "./piper_voices/en_US/voice.onnx"
VOICE_CONFIG = "./piper_voices/en_US/voice.json"

print("--- PIPER DEBUGGER ---")

# Check Executable
if os.path.exists(PIPER_EXEC):
    print(f"✅ Executable found at: {PIPER_EXEC}")
else:
    print(f"❌ Executable MISSING at: {PIPER_EXEC}")
    # Check common alternative locations
    if os.path.exists("./piper/piper"): print("   Found at ./piper/piper instead!")
    if os.path.exists("./build/piper"): print("   Found at ./build/piper instead!")

# Check Voice Model
if os.path.exists(VOICE_MODEL):
    print(f"✅ Voice Model found at: {VOICE_MODEL}")
else:
    print(f"❌ Voice Model MISSING at: {VOICE_MODEL}")

# Check Voice Config
if os.path.exists(VOICE_CONFIG):
    print(f"✅ Voice Config found at: {VOICE_CONFIG}")
else:
    print(f"❌ Voice Config MISSING at: {VOICE_CONFIG}")

print("----------------------")
