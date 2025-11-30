"use client"

import { useState, useRef } from "react"
import FileUploadArea from "./file-upload-area"
import DocumentList from "./document-list"
import { toast } from "sonner" // Assuming you have sonner or use your toast library

export default function KnowledgeBase() {
  // Store actual File objects for uploading
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  // Store file names for display
  const [documents, setDocuments] = useState<string[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFilesSelected = (files: File[]) => {
    // 1. Store the actual file objects so we can send them later
    setSelectedFiles((prev) => [...prev, ...files])
    
    // Update the display list
    const newDocs = files.map((f) => f.name)
    setDocuments((prev) => [...prev, ...newDocs])
  }

  const handleProcessDocuments = async () => {
    if (selectedFiles.length === 0) return

    setIsProcessing(true)
    try {
      // 2. Create FormData to send files
      const formData = new FormData()
      selectedFiles.forEach((file) => {
        formData.append("files", file)
      })

      // 3. Send to Python backend on port 8080
      const response = await fetch("http://localhost:8080/api/upload", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        throw new Error("Upload failed")
      }

      const result = await response.json()
      
      // Optional: Show success message
      // toast.success(`Processed ${result.files_uploaded} files!`)
      
      // Clear queue after success
      setSelectedFiles([])
      
    } catch (error) {
      console.error("Upload error:", error)
      // toast.error("Failed to process documents")
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

      {/* Process Button */}
      {documents.length > 0 && (
        <div className="space-y-4">
          <button
            onClick={handleProcessDocuments}
            disabled={isProcessing || selectedFiles.length === 0}
            className="w-full py-4 px-6 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-400 text-white text-lg font-bold rounded-xl transition-all shadow-lg hover:shadow-xl disabled:shadow-none flex items-center justify-center gap-2"
          >
            {isProcessing ? (
              <>
                <span className="inline-block animate-spin">⚙️</span>
                Processing Materials...
              </>
            ) : (
              // Change text based on if there are new files to process
              <>{selectedFiles.length > 0 ? "🔄 Index & Process Materials" : "✅ All Files Processed"}</>
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