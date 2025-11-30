"use client"

import { useState } from "react"

interface ChatMessageProps {
  message: {
    id: string
    role: "user" | "assistant"
    content: string
    images?: string[]
  }
  onImageClick: (src: string) => void
  enableReadAloud: boolean
}

export default function ChatMessage({ message, onImageClick, enableReadAloud }: ChatMessageProps) {
  const [isReadingAloud, setIsReadingAloud] = useState(false)

  const handleReadAloud = () => {
    if ("speechSynthesis" in window) {
      if (isReadingAloud) {
        speechSynthesis.cancel()
        setIsReadingAloud(false)
      } else {
        const utterance = new SpeechSynthesisUtterance(message.content)
        utterance.onend = () => setIsReadingAloud(false)
        speechSynthesis.speak(utterance)
        setIsReadingAloud(true)
      }
    }
  }

  return (
    <div className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-xs md:max-w-md lg:max-w-lg px-4 py-3 rounded-2xl ${
          message.role === "user"
            ? "bg-(--color-primary) text-white rounded-br-none"
            : "bg-(--color-bg-tertiary) text-(--color-text-primary) rounded-bl-none"
        }`}
      >
        <p className="text-sm leading-relaxed mb-2">{message.content}</p>

        {message.images && message.images.length > 0 && (
          <div className="space-y-2 mt-3">
            {message.images.map((img, idx) => (
              <img
                key={idx}
                src={img || "/placeholder.svg"}
                alt="Response diagram"
                onClick={() => onImageClick(img)}
                className="w-full rounded-lg cursor-zoom-in hover:opacity-80 transition-opacity"
              />
            ))}
          </div>
        )}

        {message.role === "assistant" && enableReadAloud && (
          <button
            onClick={handleReadAloud}
            className="mt-2 text-xs font-medium flex items-center gap-1 hover:opacity-80 transition-opacity"
          >
            {isReadingAloud ? "⏸️ Pause" : "🔊 Read aloud"}
          </button>
        )}
      </div>
    </div>
  )
}
