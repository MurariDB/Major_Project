"""
Streamlit web interface for Voice RAG Assistant (EdgeLearn Edition)
Theme: Modern Educational / LMS
"""
import os
import sys
import streamlit as st
import time
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.config import config

# Fix for Segmentation Fault on Mac M1/M2
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="EdgeLearn | AI Tutor", 
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SESSION STATE SETUP ---
if 'assistant' not in st.session_state: st.session_state.assistant = None
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'is_initialized' not in st.session_state: st.session_state.is_initialized = False
if 'current_page' not in st.session_state: st.session_state.current_page = "dashboard"
if 'study_session_start' not in st.session_state: st.session_state.study_session_start = datetime.now()

# --- 3. CUSTOM CSS (ACADEMIC THEME) ---
def apply_academic_theme():
    st.markdown("""
    <style>
        /* Import Professional Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Merriweather:wght@300;700&display=swap');

        /* Base Variables */
        :root {
            --primary-color: #2563EB; /* Royal Blue */
            --secondary-color: #F8FAFC; /* Slate White */
            --accent-color: #0F172A; /* Dark Slate */
            --success-color: #10B981;
        }

        /* Main Layout */
        .stApp {
            background-color: #F1F5F9;
            font-family: 'Inter', sans-serif;
            color: #334155;
        }

        /* Navigation Bar */
        .nav-container {
            background-color: white;
            padding: 1rem 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
        }

        /* Card Styling */
        .css-card {
            background-color: white;
            padding: 1.5rem;
            border-radius: 10px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
            margin-bottom: 1rem;
        }

        /* Typography */
        h1, h2, h3 {
            font-family: 'Merriweather', serif;
            color: var(--accent-color);
        }
        h1 { font-size: 2.5rem; }
        
        /* Custom Buttons */
        .stButton > button {
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 6px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            transition: all 0.2s;
        }
        .stButton > button:hover {
            background-color: #1D4ED8;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
        }
        
        /* Secondary Action Buttons (White) */
        div[data-testid="stHorizontalBlock"] .stButton:nth-child(2) > button {
            background-color: white;
            color: #64748B;
            border: 1px solid #CBD5E1;
        }
        div[data-testid="stHorizontalBlock"] .stButton:nth-child(2) > button:hover {
            background-color: #F8FAFC;
            color: #334155;
        }

        /* Chat Styling */
        .stChatMessage {
            background-color: white;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
        }
        .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
            background-color: #EFF6FF; /* Light Blue for User */
            border-color: #DBEAFE;
        }

        /* Hide Streamlit Boilerplate */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

apply_academic_theme()

# --- 4. CORE LOGIC ---

@st.cache_resource
def initialize_assistant():
    """Initialize the backend systems"""
    try:
        from main import VoiceRAGAssistant
        os.makedirs(config.system.pdf_dir, exist_ok=True)
        os.makedirs(config.rag.image_dir, exist_ok=True)
        return VoiceRAGAssistant(), True
    except Exception as e:
        st.error(f"System Initialization Failed: {e}")
        return None, False

def render_navbar():
    """Navigation Bar with Large Heading"""
    with st.container():
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="width: 50px; height: 50px; background: linear-gradient(135deg, #2563eb, #9333ea); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 28px; box-shadow: 0 4px 10px rgba(37, 99, 235, 0.2);">
                    ⚡
                </div>
                <div style="line-height: 1.2;">
                    <div style="background: linear-gradient(to right, #2563eb, #9333ea); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 34px; letter-spacing: -1px;">EdgeLearn</div>
                    <div style="font-size: 14px; color: #64748b; font-weight: 500;">AI-Powered Learning</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.button("📊 Dashboard", use_container_width=True):
                st.session_state.current_page = "dashboard"
                st.rerun()
        with col3:
            if st.button("📂 Library", use_container_width=True):
                st.session_state.current_page = "knowledge"
                st.rerun()
        with col4:
            if st.button("🧠 Study Room", use_container_width=True):
                st.session_state.current_page = "study"
                st.rerun()
    st.divider()

def page_dashboard():
    """Main Landing Page"""
    st.markdown("# 👋 Welcome back, Student.")
    st.markdown("Your personalized, offline AI tutor is ready.")
    
    # Fake Metrics for Demo "Educational Feel"
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Study Streak", "3 Days", "+1")
    with c2:
        # Calculate real file count if possible
        pdf_count = len(os.listdir(config.system.pdf_dir)) if os.path.exists(config.system.pdf_dir) else 0
        st.metric("Materials Indexed", f"{pdf_count} Documents", "Ready")
    with c3:
        session_mins = (datetime.now() - st.session_state.study_session_start).seconds // 60
        st.metric("Session Time", f"{session_mins} mins", "Active")

    st.markdown("### 📚 Recommended Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("#### 📂 Update Course Materials")
            st.caption("Upload new PDFs or lecture notes to the Knowledge Base.")
            if st.button("Go to Knowledge Base"):
                st.session_state.current_page = "knowledge"
                st.rerun()
    
    with col2:
        with st.container(border=True):
            st.markdown("#### 🧠 Start a Quiz / Q&A")
            st.caption("Review your materials using the Voice or Text tutor.")
            if st.button("Enter Study Room"):
                st.session_state.current_page = "study"
                st.rerun()

def page_knowledge_base():
    """Document Ingestion"""
    st.markdown("## 📂 Knowledge Base Management")
    st.info("Upload your course materials here. The AI will index text and diagrams.")

    # File Uploader
    with st.container(border=True):
        uploaded_files = st.file_uploader("Upload Course PDFs", type="pdf", accept_multiple_files=True)
        
        if uploaded_files:
            for up_file in uploaded_files:
                save_path = os.path.join(config.system.pdf_dir, up_file.name)
                if not os.path.exists(save_path):
                    with open(save_path, "wb") as f:
                        f.write(up_file.getbuffer())
                    st.toast(f"Saved {up_file.name}", icon="💾")
            
            st.divider()
            
            if st.button("🔄 Process & Index Materials", type="primary", use_container_width=True):
                if st.session_state.assistant:
                    with st.status("⚙️ Processing Knowledge Graph...", expanded=True) as status:
                        st.write("Extracting Text...")
                        st.write("Analyzing Diagrams (Computer Vision)...")
                        res = st.session_state.assistant.ingest_documents()
                        status.update(label="✅ Indexing Complete!", state="complete", expanded=False)
                    
                    st.success(f"Successfully indexed {res['text_chunks']} concepts and {res['images_indexed']} visual aids.")
                    time.sleep(1.5)
                    st.rerun()

    # Current Files List
    st.subheader("📚 Current Library")
    if os.path.exists(config.system.pdf_dir):
        files = os.listdir(config.system.pdf_dir)
        if files:
            for f in files:
                if f.endswith('.pdf'):
                    st.caption(f"📄 {f}")
        else:
            st.markdown("*No documents found.*")

    # Danger Zone
    with st.expander("⚠️ Advanced Settings"):
        if st.button("Reset Knowledge Base"):
            st.session_state.assistant.cleanup()
            st.session_state.clear()
            st.rerun()

def page_study_room():
    """Chat Interface"""
    st.markdown("## 🧠 Study Room")
    
    # Chat History Container
    chat_container = st.container(height=500)
    
    with chat_container:
        if not st.session_state.chat_history:
            st.markdown("""
            <div style='text-align: center; color: #64748B; padding: 40px;'>
                <h4>Start your session</h4>
                <p>Ask a question about your uploaded documents.</p>
            </div>
            """, unsafe_allow_html=True)
            
        for message in st.session_state.chat_history:
            role = "user" if message["role"] == "user" else "assistant"
            with st.chat_message(role):
                st.markdown(message["content"])
                
                # Render Images/Diagrams
                if role == "assistant" and message.get("images"):
                    st.markdown("---")
                    st.caption("Relevant Diagrams:")
                    cols = st.columns(3)
                    for j, img_path in enumerate(message["images"]):
                        if os.path.exists(img_path):
                            with cols[j % 3]:
                                st.image(img_path, use_container_width=True)

    # Input Area
    st.markdown("---")
    
    # Interaction Mode Selection
    mode = st.radio("Interaction Mode:", ["⌨️ Text Mode", "🎙️ Voice Mode"], horizontal=True, label_visibility="collapsed")
    
    if "Voice" in mode:
        c1, c2 = st.columns([1, 6])
        with c1:
            if st.button("🔴 Record", type="primary", use_container_width=True):
                st.session_state.assistant.stt.start_recording()
                st.toast("Listening...", icon="👂")
        with c2:
            if st.button("⏹️ Process Answer", use_container_width=True):
                with st.spinner("Transcribing & Analyzing..."):
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
                        st.error("Audio not clear. Please try again.")
    else:
        # Text Input
        if prompt := st.chat_input("Ask a question about your topic..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.write(prompt)
                
            with st.chat_message("assistant"):
                with st.spinner("Consulting Knowledge Base..."):
                    result = st.session_state.assistant.process_text_query(prompt, speak_response=True)
                    st.write(result['response'])
                    if result.get('images'):
                        st.caption("Visual Aids:")
                        img_cols = st.columns(3)
                        for i, p in enumerate(result['images']):
                             with img_cols[i%3]: st.image(p)
            
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": result['response'],
                "images": result.get('images', [])
            })
            # No rerun here to keep the flow smooth in text mode

def main():
    # --- BOOT SEQUENCE ---
    if not st.session_state.is_initialized:
        placeholder = st.empty()
        with placeholder.container():
            st.markdown("""
            <style>
            .stProgress > div > div > div > div { background-color: #2563EB; }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown("### ⚙️ Initializing EdgeLearn Core...")
            bar = st.progress(0)
            
            # Simulated loading steps
            steps = ["Loading Neural Models...", "Mounting Vector Database...", "Calibrating Audio Interface..."]
            for i, step in enumerate(steps):
                st.text(step)
                bar.progress((i + 1) * 30)
                time.sleep(0.3)
            
            assistant, success = initialize_assistant()
            if success:
                st.session_state.assistant = assistant
                st.session_state.is_initialized = True
                bar.progress(100)
                time.sleep(0.5)
            else:
                st.error("Initialization Failed. Check logs.")
                st.stop()
        placeholder.empty()

    # --- MAIN APP ROUTING ---
    render_navbar()
    
    if st.session_state.current_page == "dashboard":
        page_dashboard()
    elif st.session_state.current_page == "knowledge":
        page_knowledge_base()
    elif st.session_state.current_page == "study":
        page_study_room()

if __name__ == "__main__":
    main()