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
    <div className={`flex ${message.role === "user" ? "justify-end" : "justify-start"} gap-2 group`}>
      {message.role === "assistant" && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white text-sm flex-shrink-0 mt-1">
          🤖
        </div>
      )}

      <div
        className={`max-w-md lg:max-w-2xl px-4 py-3 rounded-2xl ${
          message.role === "user"
            ? "bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-br-none shadow-md"
            : "bg-white dark:bg-slate-800 text-gray-900 dark:text-white rounded-bl-none border border-gray-200 dark:border-slate-700 shadow-sm"
        }`}
      >
        <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">{message.content}</p>

        {message.images && message.images.length > 0 && (
          <div className="space-y-2 mt-3">
            {message.images.map((img, idx) => (
              <img
                key={idx}
                src={img || "/placeholder.svg"}
                alt="Response diagram"
                onClick={() => onImageClick(img)}
                className="w-full rounded-lg cursor-zoom-in hover:opacity-90 transition-opacity border border-gray-200 dark:border-slate-600"
              />
            ))}
          </div>
        )}

        {message.role === "assistant" && enableReadAloud && (
          <button
            onClick={handleReadAloud}
            className="mt-3 text-xs font-medium flex items-center gap-2 px-2.5 py-1.5 rounded-md bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-600 transition-colors"
          >
            {isReadingAloud ? (
              <>
                <span>⏸️</span>
                <span>Pause</span>
              </>
            ) : (
              <>
                <span>🔊</span>
                <span>Read aloud</span>
              </>
            )}
          </button>
        )}
      </div>

      {message.role === "user" && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center text-white text-sm flex-shrink-0 mt-1">
          👤
        </div>
      )}
    </div>
  )
}
