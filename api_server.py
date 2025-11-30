"""
FastAPI server to bridge the Next.js frontend with the Python backend.
Run this alongside the Next.js app to enable full AI functionality.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import sys
from typing import List
import uvicorn

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import config directly to fix the "AttributeError"
from src.utils.config import config

app = FastAPI(title="EdgeLearn API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import your main assistant
try:
    from main import VoiceRAGAssistant
    assistant = VoiceRAGAssistant()
except Exception as e:
    print(f"Warning: Could not initialize assistant: {e}")
    assistant = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "EdgeLearn API"}

@app.post("/api/chat")
async def chat(request: dict):
    """Process text query"""
    if not assistant:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        message = request.get("message", "")
        result = assistant.process_text_query(message, speak_response=False)
        return {
            "response": result.get("response", ""),
            "images": result.get("images", []),
            "success": True,
        }
    except Exception as e:
        print(f"❌ Chat Error: {e}") # Print error to terminal
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "success": False}
        )

@app.post("/api/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload and process documents"""
    if not assistant:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        saved_count = 0
        # FIX: Use the imported 'config' object, not 'assistant.config'
        pdf_dir = config.system.pdf_dir
        os.makedirs(pdf_dir, exist_ok=True)

        for file in files:
            if file.filename.endswith('.pdf'):
                save_path = os.path.join(pdf_dir, file.filename)
                
                content = await file.read()
                with open(save_path, "wb") as f:
                    f.write(content)
                saved_count += 1
        
        # Process all documents
        print(f"📂 Processing {saved_count} uploaded files...")
        result = assistant.ingest_documents()
        
        return {
            "success": True,
            "files_uploaded": saved_count,
            "text_chunks": result.get("text_chunks", 0),
            "images_indexed": result.get("images_indexed", 0),
        }
    except Exception as e:
        print(f"❌ Upload Error: {e}") # Print error to terminal
        import traceback
        traceback.print_exc() # Print full crash report
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "success": False}
        )

@app.get("/api/documents")
async def list_documents():
    """List all uploaded documents"""
    if not assistant:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    # FIX: Use the imported 'config' object
    pdf_dir = config.system.pdf_dir
    documents = []
    
    if os.path.exists(pdf_dir):
        for file in os.listdir(pdf_dir):
            if file.endswith('.pdf'):
                documents.append({
                    "name": file,
                    "path": os.path.join(pdf_dir, file),
                })
    
    return {"documents": documents, "count": len(documents)}

@app.post("/api/voice")
async def process_voice(request: dict):
    """Process voice input (audio transcription + query)"""
    if not assistant:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        result = assistant.process_voice_query()
        return {
            "transcription": result.get("query", ""),
            "response": result.get("response", ""),
            "images": result.get("images", []),
            "success": result.get("success", False),
        }
    except Exception as e:
        print(f"❌ Voice Error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "success": False}
        )

if __name__ == "__main__":
    print("🚀 Starting EdgeLearn API Server...")
    print("📝 Documentation available at http://localhost:8080/docs")
    # Changed port to 8080 to match your setup
    uvicorn.run(app, host="0.0.0.0", port=8080)