"use client"

import { useState, useRef } from "react"
import FileUploadArea from "./file-upload-area"
import DocumentList from "./document-list"

export default function KnowledgeBase() {
  const [documents, setDocuments] = useState<string[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFilesSelected = (files: File[]) => {
    const newDocs = files.map((f) => f.name)
    setDocuments((prev) => [...prev, ...newDocs])
  }

  const handleProcessDocuments = async () => {
    setIsProcessing(true)
    // Simulate processing
    await new Promise((resolve) => setTimeout(resolve, 2000))
    setIsProcessing(false)
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

      {/* Process Button */}
      {documents.length > 0 && (
        <div className="space-y-4">
          <button
            onClick={handleProcessDocuments}
            disabled={isProcessing}
            className="w-full btn btn-primary text-lg py-3 text-white font-bold"
          >
            {isProcessing ? (
              <>
                <span className="inline-block animate-spin">⚙️</span>
                Processing Materials...
              </>
            ) : (
              <>🔄 Index & Process Materials</>
            )}
          </button>

          {isProcessing && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-(--color-text-secondary)">
                <span>Extracting text from PDFs...</span>
              </div>
              <div className="w-full h-2 bg-(--color-bg-tertiary) rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-(--color-primary) to-(--color-accent) animate-pulse" />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Document List */}
      {documents.length > 0 && (
        <div className="space-y-4">
          <h2 className="font-serif font-bold text-xl">Uploaded Documents</h2>
          <DocumentList documents={documents} />
        </div>
      )}

      {documents.length === 0 && !isProcessing && (
        <div className="text-center py-12 text-(--color-text-tertiary)">
          <p className="text-lg">No documents yet. Start by uploading your first PDF.</p>
        </div>
      )}
    </div>
  )
}
