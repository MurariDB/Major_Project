"use client"

import { useState } from "react"

interface ImageZoomModalProps {
  image: string
  onClose: () => void
}

export default function ImageZoomModal({ image, onClose }: ImageZoomModalProps) {
  const [zoom, setZoom] = useState(1)

  const handleZoom = (direction: "in" | "out") => {
    setZoom((prev) => {
      const newZoom = direction === "in" ? prev + 0.2 : prev - 0.2
      return Math.max(0.5, Math.min(3, newZoom))
    })
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-(--color-bg-secondary) rounded-xl p-6 max-w-3xl w-full max-h-[90vh] overflow-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Toolbar */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-(--color-text-primary)">Image Viewer</h3>
          <div className="flex items-center gap-2">
            <button onClick={() => handleZoom("out")} className="btn btn-secondary px-3" disabled={zoom <= 0.5}>
              −
            </button>
            <span className="text-sm font-medium w-12 text-center text-(--color-text-secondary)">
              {Math.round(zoom * 100)}%
            </span>
            <button onClick={() => handleZoom("in")} className="btn btn-secondary px-3" disabled={zoom >= 3}>
              +
            </button>
            <button onClick={onClose} className="btn btn-secondary px-3 ml-2">
              ✕
            </button>
          </div>
        </div>

        {/* Image */}
        <div className="flex items-center justify-center bg-(--color-bg-tertiary) rounded-lg overflow-auto h-[60vh]">
          <img
            src={image || "/placeholder.svg"}
            alt="Zoomed"
            style={{ transform: `scale(${zoom})`, transition: "transform 0.2s" }}
            className="cursor-move"
          />
        </div>

        {/* Controls Info */}
        <p className="text-xs text-(--color-text-tertiary) mt-4 text-center">
          Use the buttons above to zoom in and out
        </p>
      </div>
    </div>
  )
}
