"use client"

import type React from "react"

import { useState, type RefObject } from "react"

interface FileUploadAreaProps {
  onFilesSelected: (files: File[]) => void
  fileInputRef: RefObject<HTMLInputElement>
}

export default function FileUploadArea({ onFilesSelected, fileInputRef }: FileUploadAreaProps) {
  const [isDragging, setIsDragging] = useState(false)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const files = Array.from(e.dataTransfer.files).filter((f) => f.type === "application/pdf")
    onFilesSelected(files)
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      onFilesSelected(Array.from(e.target.files))
    }
  }

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`border-2 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer ${
        isDragging
          ? "border-(--color-primary) bg-(--color-primary)/5 scale-105"
          : "border-(--color-border) bg-(--color-bg-secondary) hover:border-(--color-primary) hover:bg-(--color-primary)/5"
      }`}
      onClick={() => fileInputRef.current?.click()}
    >
      <div className="text-5xl mb-4">📤</div>
      <h3 className="font-serif font-bold text-xl mb-2 text-(--color-text-primary)">Drop your PDFs here</h3>
      <p className="text-(--color-text-secondary) mb-4">or click to browse your files</p>
      <p className="text-xs text-(--color-text-tertiary)">Supported format: PDF files only</p>

      <input ref={fileInputRef} type="file" multiple accept=".pdf" onChange={handleFileSelect} className="hidden" />
    </div>
  )
}
