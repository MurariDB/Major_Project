"use client"

import { useState, useRef } from "react"
import FileUploadArea from "./file-upload-area"
import DocumentList from "./document-list"
import ProcessingResults from "./processing_results"

export default function KnowledgeBase() {
  const [documents, setDocuments] = useState<string[]>(["Final_Major_Projectpp (1).pdf"])
  const [isProcessing, setIsProcessing] = useState(false)
  const [showResults, setShowResults] = useState(false)
  const [error, setError] = useState<string>("")
  const [processingStats, setProcessingStats] = useState({
    text_chunks: 0,
    images_indexed: 0,
    duration: 0,
    text_collection_count: 0,
    image_collection_count: 0,
    db_path: "./knowledge_base.db",
    faiss_index_path: "./faiss_index.idx",
    id_map_path: "./id_map.json",
    pdf_directory: "./data/pdfs",
    images_directory: "./data/images",
  })
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const handleFilesSelected = (files: File[]) => {
    const newDocs = files.map((f) => f.name)
    setDocuments((prev) => [...prev, ...newDocs])
    setError("")
  }

  const handleProcessDocuments = async () => {
    setIsProcessing(true)
    setError("")
    try {
      const formData = new FormData()

      if (!fileInputRef.current?.files || fileInputRef.current.files.length === 0) {
        setError("No files to process. Please upload PDFs first.")
        setIsProcessing(false)
        return
      }

      Array.from(fileInputRef.current.files).forEach((file) => {
        formData.append("files", file)
      })

      const response = await fetch("http://localhost:8080/api/upload", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || `Upload failed with status ${response.status}`)
      }

      const data = await response.json()

      if (data.success) {
        setProcessingStats({
          text_chunks: data.text_chunks || 0,
          images_indexed: data.images_indexed || 0,
          duration: data.duration || 2.5,
          text_collection_count: data.text_chunks || 0,
          image_collection_count: data.images_indexed || 0,
          db_path: "./knowledge_base.db",
          faiss_index_path: "./faiss_index.idx",
          id_map_path: "./id_map.json",
          pdf_directory: "./data/pdfs",
          images_directory: "./data/images",
        })
        setShowResults(true)
      } else {
        setError(data.error || "Processing failed")
      }
    } catch (error) {
      console.error("Processing error:", error)
      setError(error instanceof Error ? error.message : "An error occurred during processing")
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="space-y-8 animate-fadeInUp max-w-4xl">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-4xl font-bold text-(--color-text-primary)">📚 Knowledge Base</h1>
        <p className="text-(--color-text-secondary)">
          Upload your course materials. The AI will index text, diagrams, and concepts.
        </p>
      </div>

      {/* Upload Area */}
      <FileUploadArea onFilesSelected={handleFilesSelected} fileInputRef={fileInputRef} />

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}

      {/* Document List - comes before process button */}
      {documents.length > 0 && (
        <div className="space-y-4">
          <h2 className="font-serif font-bold text-xl">Uploaded Documents</h2>
          <DocumentList documents={documents} />
        </div>
      )}

      {documents.length > 0 && (
        <div className="space-y-4">
          <button
            onClick={handleProcessDocuments}
            disabled={isProcessing}
            className="w-full py-4 px-6 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-400 text-white text-lg font-bold rounded-xl transition-all shadow-lg hover:shadow-xl disabled:shadow-none flex items-center justify-center gap-2"
          >
            {isProcessing ? (
              <>
                <span className="inline-block animate-spin">⚙️</span>
                <span>Processing Materials...</span>
              </>
            ) : (
              <>
                <span>🔄</span>
                <span>Index & Process Materials</span>
              </>
            )}
          </button>

          {isProcessing && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-(--color-text-secondary)">
                <span>Extracting text from PDFs...</span>
              </div>
              <div className="w-full h-2 bg-(--color-bg-tertiary) rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-blue-500 to-purple-600 animate-pulse" />
              </div>
            </div>
          )}
        </div>
      )}

      {documents.length === 0 && !isProcessing && (
        <div className="text-center py-12 text-(--color-text-tertiary)">
          <p className="text-lg">No documents yet. Start by uploading your first PDF.</p>
        </div>
      )}

      <ProcessingResults stats={processingStats} isVisible={showResults} onClose={() => setShowResults(false)} />
    </div>
  )
}
