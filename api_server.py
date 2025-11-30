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

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

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
        for file in files:
            if file.filename.endswith('.pdf'):
                pdf_dir = assistant.config.system.pdf_dir
                os.makedirs(pdf_dir, exist_ok=True)
                save_path = os.path.join(pdf_dir, file.filename)
                
                content = await file.read()
                with open(save_path, "wb") as f:
                    f.write(content)
                saved_count += 1
        
        # Process all documents
        result = assistant.ingest_documents()
        
        return {
            "success": True,
            "files_uploaded": saved_count,
            "text_chunks": result.get("text_chunks", 0),
            "images_indexed": result.get("images_indexed", 0),
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "success": False}
        )

@app.get("/api/documents")
async def list_documents():
    """List all uploaded documents"""
    if not assistant:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    pdf_dir = assistant.config.system.pdf_dir
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
        # The audio would come as base64 or file reference
        result = assistant.process_voice_query()
        return {
            "transcription": result.get("query", ""),
            "response": result.get("response", ""),
            "images": result.get("images", []),
            "success": result.get("success", False),
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "success": False}
        )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting EdgeLearn API Server...")
    print("📝 Documentation available at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
