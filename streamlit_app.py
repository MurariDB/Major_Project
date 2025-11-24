"""
Streamlit web interface for Voice RAG Assistant (Modern UI Edition)
"""
import os
import sys
import streamlit as st
import time
from PIL import Image

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.config import config

# Fix for Segmentation Fault on Mac M1/M2
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

# Page configuration
st.set_page_config(
    page_title="Hybrid RAG", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if 'assistant' not in st.session_state: st.session_state.assistant = None
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'is_initialized' not in st.session_state: st.session_state.is_initialized = False
if 'voice_mode' not in st.session_state: st.session_state.voice_mode = False

@st.cache_resource
def initialize_assistant():
    """Initialize the assistant (cached)"""
    try:
        from main import VoiceRAGAssistant
        # Ensure directories exist
        os.makedirs(config.system.pdf_dir, exist_ok=True)
        os.makedirs(config.rag.image_dir, exist_ok=True)
        
        assistant = VoiceRAGAssistant()
        return assistant, True
    except Exception as e:
        st.error(f"Failed to initialize: {e}")
        return None, False

def main():
    # --- Sidebar: Configuration & Status ---
    with st.sidebar:
        st.title("🎛️ Controls")
        
        # 1. Document Management
        st.subheader("📁 Documents")
        uploaded_files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
        
        if uploaded_files:
            for up_file in uploaded_files:
                save_path = os.path.join(config.system.pdf_dir, up_file.name)
                if not os.path.exists(save_path):
                    with open(save_path, "wb") as f:
                        f.write(up_file.getbuffer())
                    st.toast(f"Saved {up_file.name}", icon="💾")
            
            if st.button("🔄 Ingest Documents", type="primary", use_container_width=True):
                if st.session_state.assistant:
                    with st.spinner("Indexing text & images..."):
                        res = st.session_state.assistant.ingest_documents()
                        st.success(f"Indexed {res['text_chunks']} chunks & {res['images_indexed']} images")
                        time.sleep(1)
                        st.rerun()

        st.divider()

        # 2. Voice Settings
        st.subheader("🎙️ Voice Interaction")
        st.session_state.voice_mode = st.toggle("Enable Voice Input Mode", value=False)
        
        if os.path.exists("voice_input.wav"):
            st.caption("✅ Voice Cloning Active (Coqui)")
        else:
            st.caption("ℹ️ Using Piper TTS (Fast)")

        st.divider()
        
        # 3. System Actions
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

        if st.button("🧹 Reset System", use_container_width=True):
            if st.session_state.assistant:
                st.session_state.assistant.cleanup()
            st.session_state.clear()
            st.rerun()

    # --- Main Area: Initialization ---
    if not st.session_state.is_initialized:
        st.info("🚀 Initializing Hybrid RAG System... (This loads AI models)")
        assistant, success = initialize_assistant()
        if success:
            st.session_state.assistant = assistant
            st.session_state.is_initialized = True
            st.rerun()
        else:
            st.stop()

    st.title("🤖 Hybrid Voice Assistant")
    st.caption("Ask questions about your documents using Text or Voice. Images will appear below relevant answers.")

    # --- Chat History Display ---
    for i, message in enumerate(st.session_state.chat_history):
        role = "user" if message["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.markdown(message["content"])
            
            # Extras for Assistant messages
            if role == "assistant":
                # 1. Render Images (FIXED: Using File Paths)
                if message.get("images"):
                    st.markdown("---")
                    st.markdown("**Relevant Images:**")
                    cols = st.columns(3)
                    for j, img_path in enumerate(message["images"]):
                        if os.path.exists(img_path):
                            with cols[j % 3]:
                                # PASS PATH STRING, NOT PIL IMAGE OBJECT
                                st.image(img_path, width="stretch", caption=f"Source: {os.path.basename(img_path)}")
                        else:
                            st.caption(f"⚠️ Image missing: {os.path.basename(img_path)}")
                
                # 2. Read Aloud Button
                if st.button("🔊 Read Aloud", key=f"read_btn_{i}"):
                    st.toast("Generating audio...", icon="🔊")
                    st.session_state.assistant.tts.speak(message["content"])

    # --- Input Area ---
    
    if st.session_state.voice_mode:
        container = st.container(border=True)
        with container:
            c1, c2 = st.columns([1, 4])
            with c1:
                if st.button("🎤 Record", use_container_width=True, type="primary"):
                    st.session_state.assistant.stt.start_recording()
                    st.toast("Recording started...", icon="🔴")
            
            with c2:
                if st.button("⏹️ Stop & Ask", use_container_width=True):
                    with st.spinner("Transcribing & Thinking..."):
                        st.session_state.assistant.stt.stop_recording()
                        result = st.session_state.assistant.process_voice_query()
                        
                        if result['success']:
                            user_text = result.get('query', result.get('transcription', ''))
                            st.session_state.chat_history.append({"role": "user", "content": user_text})
                            st.session_state.chat_history.append({
                                "role": "assistant", 
                                "content": result['response'],
                                "images": result.get('images', [])
                            })
                            st.rerun()
                        else:
                            st.error("Could not understand audio or no speech detected.")

    else:
        if prompt := st.chat_input("Ask a question about your PDFs..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # speak_response=True will trigger auto-play from backend
                    result = st.session_state.assistant.process_text_query(prompt, speak_response=True)
                    
                    st.markdown(result['response'])
                    
                    if result.get('images'):
                        st.markdown("---")
                        st.markdown("**Relevant Images:**")
                        cols = st.columns(3)
                        for i, img_path in enumerate(result['images']):
                            if os.path.exists(img_path):
                                with cols[i % 3]:
                                    # PASS PATH STRING
                                    st.image(img_path, width="stretch")
            
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": result['response'],
                "images": result.get('images', [])
            })
            st.rerun()

if __name__ == "__main__":
    main()