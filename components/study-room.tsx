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
  const messagesContainerRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

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
      content: `I understand you asked about "${inputValue}". Based on your materials, here's what I found... [This would be replaced with actual AI response]`,
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
    <div className="h-screen flex flex-col bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      {/* Modern Header */}
      <div className="border-b border-gray-200 dark:border-slate-700 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center text-white font-bold">
                🧠
              </div>
              <div>
                <h1 className="font-semibold text-gray-900 dark:text-white text-lg">Study Room</h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">Interactive learning with your AI tutor</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* Mode Selector */}
              <div className="flex gap-1 bg-gray-100 dark:bg-slate-800 p-1 rounded-lg">
                {(["text", "voice"] as const).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => setInteractionMode(mode)}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                      interactionMode === mode
                        ? "bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-sm"
                        : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
                    }`}
                  >
                    {mode === "text" ? "⌨️ Text" : "🎙️ Voice"}
                  </button>
                ))}
              </div>

              {/* Read Aloud Button */}
              <button
                onClick={() => setEnableReadAloud(!enableReadAloud)}
                className={`p-2.5 rounded-lg transition-all ${
                  enableReadAloud
                    ? "bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400"
                    : "bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-slate-700"
                }`}
                title={enableReadAloud ? "Read-aloud enabled" : "Read-aloud disabled"}
              >
                🔊
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Area - Modern scrollable */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto max-w-6xl w-full mx-auto px-4 py-6 space-y-4 scroll-smooth"
      >
        <div className="space-y-4">
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
              <div className="max-w-md">
                <div className="bg-white dark:bg-slate-800 rounded-2xl rounded-bl-none shadow-sm border border-gray-100 dark:border-slate-700 p-4 flex gap-2">
                  <div className="w-2 h-2 rounded-full bg-gray-400 dark:bg-gray-500 animate-bounce" />
                  <div
                    className="w-2 h-2 rounded-full bg-gray-400 dark:bg-gray-500 animate-bounce"
                    style={{ animationDelay: "150ms" }}
                  />
                  <div
                    className="w-2 h-2 rounded-full bg-gray-400 dark:bg-gray-500 animate-bounce"
                    style={{ animationDelay: "300ms" }}
                  />
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>
      </div>

      {/* Modern Input Area */}
      <div className="border-t border-gray-200 dark:border-slate-700 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl p-4">
        <div className="max-w-6xl mx-auto">
          {interactionMode === "voice" ? (
            <VoiceInput onInput={handleVoiceInput} onSend={handleSendMessage} />
          ) : (
            <div className="flex gap-3">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && !isLoading && handleSendMessage()}
                placeholder="Ask me anything about your materials..."
                className="flex-1 px-4 py-3 bg-gray-100 dark:bg-slate-800 border border-gray-300 dark:border-slate-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-all"
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isLoading}
                className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-400 text-white font-medium rounded-xl transition-all shadow-lg hover:shadow-xl disabled:shadow-none"
              >
                Send
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
