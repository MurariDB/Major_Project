"""
FastAPI server to bridge the Next.js frontend with the Python backend.
Run this alongside the Next.js app to enable full AI functionality.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
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

class ChatRequest(BaseModel):
    message: str

class VoiceRequest(BaseModel):
    transcription: str

# Import your main assistant and config
try:
    from main import VoiceRAGAssistant
    from src.utils.config import config
    assistant = VoiceRAGAssistant()
except Exception as e:
    print(f"Warning: Could not initialize assistant: {e}")
    assistant = None
    config = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "EdgeLearn API"}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Process text query"""
    if not assistant:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        message = request.message
        print(f"[API] Processing chat: {message}")
        result = assistant.process_text_query(message, speak_response=False)
        return {
            "response": result.get("response", ""),
            "images": result.get("images", []),
            "success": True,
        }
    except Exception as e:
        print(f"[API] Chat error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "success": False}
        )

@app.post("/api/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload and process documents"""
    if not assistant or not config:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        saved_count = 0
        if not files or len(files) == 0:
            return JSONResponse(
                status_code=400,
                content={"error": "No files provided", "success": False}
            )
        
        for file in files:
            if file.filename and file.filename.endswith('.pdf'):
                pdf_dir = config.system.pdf_dir
                os.makedirs(pdf_dir, exist_ok=True)
                save_path = os.path.join(pdf_dir, file.filename)
                
                content = await file.read()
                with open(save_path, "wb") as f:
                    f.write(content)
                saved_count += 1
        
        if saved_count == 0:
            return JSONResponse(
                status_code=400,
                content={"error": "No valid PDF files found", "success": False}
            )
        
        # Process all documents
        result = assistant.ingest_documents()
        
        return {
            "success": True,
            "files_uploaded": saved_count,
            "text_chunks": result.get("text_chunks", 0),
            "images_indexed": result.get("images_indexed", 0),
            "duration": result.get("duration", 0),
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "success": False}
        )

@app.get("/api/documents")
async def list_documents():
    """List all uploaded documents"""
    if not assistant or not config:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
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
async def process_voice(request: VoiceRequest):
    """Process voice input (transcription to query)"""
    if not assistant:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        transcription = request.transcription
        print(f"[API] Processing voice: {transcription}")
        result = assistant.process_text_query(transcription, speak_response=False)
        return {
            "transcription": transcription,
            "response": result.get("response", ""),
            "images": result.get("images", []),
            "success": True,
        }
    except Exception as e:
        print(f"[API] Voice error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "success": False}
        )

@app.get("/api/database-stats")
async def get_database_stats():
    """Get database statistics and schema info"""
    if not assistant or not config:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        stats = {
            "text_collection_count": assistant.vector_db.get_text_collection_count(),
            "image_collection_count": assistant.vector_db.get_image_collection_count(),
            "db_path": config.rag.image_db_path,
            "faiss_index_path": "./faiss_index.idx",
            "id_map_path": "./id_map.json",
            "pdf_directory": config.system.pdf_dir,
            "images_directory": config.rag.image_dir,
        }
        return stats
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting EdgeLearn API Server...")
    print("📝 Documentation available at http://localhost:8080/docs")
    uvicorn.run(app, host="0.0.0.0", port=8080)
