import os
import sys
import shutil
import time
import base64
import sqlite3
import json
import subprocess
import tempfile
import gradio as gr
from PIL import Image
from typing import List, Tuple

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from main import VoiceRAGAssistant
from src.utils.config import config

# Initialize the global assistant instance
# We initialize it once when the app starts
try:
    print("🚀 Initializing Backend System...")
    assistant = VoiceRAGAssistant()
    # Ensure directories exist
    os.makedirs(config.system.pdf_dir, exist_ok=True)
    os.makedirs(config.rag.image_dir, exist_ok=True)
except Exception as e:
    print(f"❌ Failed to initialize assistant: {e}")
    assistant = None

# ============================================================================
# HELPER FUNCTIONS (Adapters for your specific backend)
# ============================================================================

def get_db_connection():
    """Helper to get a read-only connection to your specific SQLite DB"""
    return sqlite3.connect(config.rag.image_db_path, check_same_thread=False)

def tts_to_file(text: str) -> str:
    """
    Adapts your TextToSpeech logic to return a file path for Gradio 
    instead of playing it immediately via system audio.
    """
    if not text or not assistant: return None
    
    # Reuse configuration from your existing TextToSpeech class
    piper_exe = assistant.tts.PIPER_EXECUTABLE if hasattr(assistant.tts, 'PIPER_EXECUTABLE') else os.path.join(os.getcwd(), "piper", "build", "piper")
    model_path = assistant.tts.PIPER_MODEL_PATH if hasattr(assistant.tts, 'PIPER_MODEL_PATH') else os.path.join(os.getcwd(), "piper_voices", "en_US", "voice.onnx")
    config_path = assistant.tts.PIPER_CONFIG_PATH if hasattr(assistant.tts, 'PIPER_CONFIG_PATH') else os.path.join(os.getcwd(), "piper_voices", "en_US", "voice.json")
    espeak_data = assistant.tts.ESPEAK_DATA if hasattr(assistant.tts, 'ESPEAK_DATA') else os.path.join(os.getcwd(), "piper", "espeak-ng-data")

    if not os.path.exists(piper_exe):
        print(f"⚠️ Piper executable not found at {piper_exe}")
        return None

    try:
        # Create temp file
        fd, output_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)

        length_scale = str(1.0 / (config.audio.tts_rate / 100.0))
        
        command = [
            piper_exe,
            "--model", model_path,
            "--config", config_path,
            "--output_file", output_path,
            "--length_scale", length_scale,
            "--espeak_data", espeak_data
        ]
        
        # Handle MacOS dynamic libraries if needed (copied from your src code)
        lib_path = os.path.dirname(piper_exe)
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
        return output_path
    except Exception as e:
        print(f"❌ TTS Generation Error: {e}")
        return None

def get_stats_from_db():
    """Queries your VectorDatabase for statistics"""
    stats = {
        'paragraphs': 0, 'images': 0, 'tags': 0, 
        'total_pages': 0, 'pdf_sources': []
    }
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats['paragraphs'] = cursor.execute("SELECT COUNT(*) FROM paragraphs").fetchone()[0]
        stats['images'] = cursor.execute("SELECT COUNT(*) FROM images").fetchone()[0]
        
        # Get unique tags (stored as JSON strings, so this is an approximation or requires parsing)
        # For speed, we just count relationships of type 'HAS_TAG'
        stats['tags'] = cursor.execute("SELECT COUNT(DISTINCT target_id) FROM relationships WHERE type='HAS_TAG'").fetchone()[0]
        
        # Sources
        sources = cursor.execute("SELECT DISTINCT source_pdf FROM paragraphs").fetchall()
        stats['pdf_sources'] = [s[0] for s in sources]
        
        conn.close()
    except Exception as e:
        print(f"Stat fetch error: {e}")
    return stats

def search_tags_in_db(tag_query):
    """Searches your DB for content with specific tags"""
    results = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Find paragraphs linked to this tag
        query = """
            SELECT p.header, p.page_num, p.text, p.source_pdf 
            FROM paragraphs p
            JOIN relationships r ON p.id = r.source_id
            WHERE r.type = 'HAS_TAG' AND r.target_id LIKE ?
            LIMIT 10
        """
        rows = cursor.execute(query, (f"%{tag_query}%",)).fetchall()
        for r in rows:
            results.append({
                "header": r[0], "page": r[1], "text": r[2], "source": r[3]
            })
        conn.close()
    except Exception as e:
        print(f"Tag search error: {e}")
    return results

def get_all_tags():
    """Get list of available tags"""
    tags = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        rows = cursor.execute("""
            SELECT target_id, COUNT(*) as cnt 
            FROM relationships 
            WHERE type='HAS_TAG' 
            GROUP BY target_id 
            ORDER BY cnt DESC 
            LIMIT 50
        """).fetchall()
        tags = [(r[0], r[1]) for r in rows]
        conn.close()
    except: pass
    return tags

# ============================================================================
# GRADIO INTERFACE FUNCTIONS
# ============================================================================

def process_upload(files):
    if not files:
        return "⚠️ No files selected.", []
    
    if not assistant:
        return "❌ Assistant not initialized. Check console for errors.", []

    try:
        # 1. Move files to configured PDF directory
        saved_files = []
        for file_obj in files:
            # Gradio passes file_obj as a NamedString or similar wrapper
            dest_path = os.path.join(config.system.pdf_dir, os.path.basename(file_obj.name))
            shutil.copy(file_obj.name, dest_path)
            saved_files.append(os.path.basename(file_obj.name))
        
        # 2. Trigger Ingestion
        ingest_res = assistant.ingest_documents()
        
        msg = f"✅ Processed {len(saved_files)} files.\n"
        msg += f"📊 Text Chunks: {ingest_res['text_chunks']}\n"
        msg += f"🖼️ Images Indexed: {ingest_res['images_indexed']}\n"
        msg += f"⏱️ Time: {ingest_res['duration']:.2f}s"
        
        return msg, saved_files
    except Exception as e:
        return f"❌ Error: {str(e)}", []

def chat_response(user_text, user_audio, history):
    if not assistant:
        history.append((user_text or "Audio Input", "❌ System not initialized."))
        yield history, None, []
        return

    # 1. Handle Input (Text or Audio)
    query = user_text
    if user_audio:
        # Use your existing STT class to transcribe the file
        # stt.transcribe_audio expects numpy array, but we have a filepath. 
        # Easier to just use SpeechToText's internal logic or a simple load
        # For simplicity, let's use the text input if provided, else simple transcription fallback
        # Or better: Read file using librosa/scipy and pass to stt.transcribe_audio
        try:
            import librosa
            audio_data, _ = librosa.load(user_audio, sr=config.audio.sample_rate)
            query = assistant.stt.transcribe_audio(audio_data)
        except ImportError:
            query = "[Error: Librosa not installed for audio file loading]"
        except Exception as e:
            query = f"[Audio Processing Error: {e}]"

    if not query:
        yield history, None, []
        return

    # Update history with user query
    history = history + [[query, None]]
    yield history, None, []

    # 2. Process Query (RAG)
    # speak_response=False because we handle audio separately for Gradio
    result = assistant.process_text_query(query, speak_response=False)
    
    response_text = result['response']
    image_paths = result.get('images', [])

    # 3. Generate Audio Response (Offline File)
    audio_path = tts_to_file(response_text)

    # 4. Prepare Images for Gallery
    # Gradio Gallery accepts file paths directly
    gallery_images = []
    for img_path in image_paths:
        if os.path.exists(img_path):
            gallery_images.append((img_path, os.path.basename(img_path)))

    # Update history with bot response
    history[-1][1] = response_text
    
    yield history, audio_path, gallery_images

def render_stats():
    s = get_stats_from_db()
    text = f"""
    ### 📊 Knowledge Base Status
    - **Total Documents:** {len(s['pdf_sources'])}
    - **Text Sections:** {s['paragraphs']}
    - **Indexed Images:** {s['images']}
    - **Knowledge Tags:** {s['tags']}
    
    ### 📂 Active Files
    """
    for pdf in s['pdf_sources']:
        text += f"- {pdf}\n"
    return text

def search_tags_ui(tag):
    if not tag: return "Enter a tag to search."
    res = search_tags_in_db(tag)
    if not res: return f"No results found for tag: '{tag}'"
    
    out = ""
    for r in res:
        out += f"**{r['header']}** (Page {r['page']})\n_{r['text'][:150]}..._\n\n"
    return out

def show_avail_tags():
    tags = get_all_tags()
    return ", ".join([f"{t[0]} ({t[1]})" for t in tags])

# ============================================================================
# MAIN GRADIO APP
# ============================================================================

with gr.Blocks(title="Voice RAG Assistant", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🤖 Hybrid Voice RAG Assistant")
    gr.Markdown("Chat with your documents using AI. Upload PDFs, ask questions via text or voice.")

    with gr.Tabs():
        # --- TAB 1: UPLOAD ---
        with gr.Tab("📁 Document Management"):
            with gr.Row():
                with gr.Column():
                    file_up = gr.File(label="Upload PDFs", file_count="multiple", file_types=[".pdf"])
                    ingest_btn = gr.Button("🚀 Ingest Documents", variant="primary")
                with gr.Column():
                    upload_log = gr.Textbox(label="Processing Log", lines=10)
            
            ingest_btn.click(process_upload, inputs=[file_up], outputs=[upload_log, gr.State()])

        # --- TAB 2: CHAT ---
        with gr.Tab("💬 Voice/Text Chat"):
            chatbot = gr.Chatbot(height=500, label="Conversation")
            
            with gr.Row():
                with gr.Column(scale=3):
                    msg_input = gr.Textbox(label="Type your question", placeholder="What does the document say about...")
                    audio_input = gr.Audio(sources=["microphone"], type="filepath", label="Or speak your question")
                with gr.Column(scale=1):
                    submit_btn = gr.Button("Send", variant="primary")
                    clear_btn = gr.Button("Clear Chat")
            
            with gr.Row():
                audio_output = gr.Audio(label="Assistant Voice Response", autoplay=True)
                image_gallery = gr.Gallery(label="Retrieved Images", columns=3, height="auto")

            # Interactions
            submit_btn.click(
                chat_response, 
                inputs=[msg_input, audio_input, chatbot], 
                outputs=[chatbot, audio_output, image_gallery]
            )
            msg_input.submit(
                chat_response, 
                inputs=[msg_input, audio_input, chatbot], 
                outputs=[chatbot, audio_output, image_gallery]
            )
            clear_btn.click(lambda: [], None, chatbot, queue=False)

        # --- TAB 3: TAGS ---
        with gr.Tab("🏷️ Tag Search"):
            with gr.Row():
                tag_in = gr.Textbox(label="Search by Tag", placeholder="e.g. introduction, methodology")
                tag_btn = gr.Button("Search")
                list_tags_btn = gr.Button("List Available Tags")
            
            tag_res = gr.Markdown("Results will appear here...")
            
            tag_btn.click(search_tags_ui, inputs=[tag_in], outputs=[tag_res])
            list_tags_btn.click(show_avail_tags, outputs=[tag_res])

        # --- TAB 4: STATS ---
        with gr.Tab("📊 Statistics"):
            refresh_btn = gr.Button("🔄 Refresh Stats")
            stats_view = gr.Markdown(render_stats())
            refresh_btn.click(render_stats, outputs=[stats_view])

if __name__ == "__main__":
    demo.launch(share=False)