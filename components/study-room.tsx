"use client"

import { useState, useRef, useEffect } from "react"
import ChatMessage from "./chat-message"
import VoiceInput from "./voice-input"
import ImageZoomModal from "./image-zoom-modal"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  images?: string[]
  timestamp: Date
}

export default function StudyRoom() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "Hello! I'm your AI tutor. Ask me anything about your uploaded materials or any topic you'd like to learn about.",
      timestamp: new Date(),
    },
  ])
  const [inputValue, setInputValue] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [interactionMode, setInteractionMode] = useState<"text" | "voice">("text")
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [enableReadAloud, setEnableReadAloud] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: inputValue,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputValue("")
    setIsLoading(true)

    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1500))

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content: `I understand you asked about "${inputValue}". Based on your materials, here\'s what I found... [This would be replaced with actual AI response]`,
      images: Math.random() > 0.5 ? ["/abstract-diagram.png"] : undefined,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, assistantMessage])
    setIsLoading(false)

    // Text-to-speech if enabled
    if (enableReadAloud && "speechSynthesis" in window) {
      const utterance = new SpeechSynthesisUtterance(assistantMessage.content)
      speechSynthesis.speak(utterance)
    }
  }

  const handleVoiceInput = (text: string) => {
    setInputValue(text)
  }

  return (
    <div className="h-screen max-h-screen flex flex-col bg-(--color-bg-primary) animate-fadeInUp">
      {/* Header */}
      <div className="bg-(--color-bg-secondary) border-b border-(--color-border) p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-(--color-text-primary)">🧠 Study Room</h1>
              <p className="text-sm text-(--color-text-secondary)">Interactive learning with your AI tutor</p>
            </div>
            <button
              onClick={() => setEnableReadAloud(!enableReadAloud)}
              className={`btn btn-icon transition-all ${
                enableReadAloud
                  ? "bg-(--color-success) text-white"
                  : "bg-(--color-bg-tertiary) text-(--color-text-secondary)"
              }`}
              title="Toggle read-aloud"
            >
              🔊
            </button>
          </div>

          {/* Mode Selector */}
          <div className="flex gap-2">
            {(["text", "voice"] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => setInteractionMode(mode)}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  interactionMode === mode
                    ? "bg-(--color-primary) text-white"
                    : "bg-(--color-bg-tertiary) text-(--color-text-secondary) hover:bg-(--color-border)"
                }`}
              >
                {mode === "text" ? "⌨️ Text Mode" : "🎙️ Voice Mode"}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto max-w-4xl w-full mx-auto px-4 py-6 space-y-4">
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message}
            onImageClick={setSelectedImage}
            enableReadAloud={enableReadAloud}
          />
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-(--color-bg-tertiary) rounded-2xl rounded-tl-none p-4 max-w-xs">
              <div className="flex gap-2">
                <div className="w-3 h-3 rounded-full bg-(--color-text-tertiary) animate-pulse" />
                <div
                  className="w-3 h-3 rounded-full bg-(--color-text-tertiary) animate-pulse"
                  style={{ animationDelay: "150ms" }}
                />
                <div
                  className="w-3 h-3 rounded-full bg-(--color-text-tertiary) animate-pulse"
                  style={{ animationDelay: "300ms" }}
                />
              </div>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input Area */}
      <div className="bg-(--color-bg-secondary) border-t border-(--color-border) p-4">
        <div className="max-w-4xl mx-auto">
          {interactionMode === "voice" ? (
            <VoiceInput onInput={handleVoiceInput} onSend={handleSendMessage} />
          ) : (
            <div className="flex gap-3">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
                placeholder="Ask me anything about your materials..."
                className="input flex-1"
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isLoading}
                className="btn btn-primary px-6"
              >
                Send →
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Image Zoom Modal */}
      {selectedImage && <ImageZoomModal image={selectedImage} onClose={() => setSelectedImage(null)} />}
    </div>
  )
}
