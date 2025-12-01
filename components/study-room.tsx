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
    const currentInput = inputValue
    setInputValue("")
    setIsLoading(true)

    try {
      console.log("[Study Room] Sending message:", currentInput)
      
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: currentInput }),
      })

      console.log("[Study Room] Response status:", response.status)

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || `Server error: ${response.status}`)
      }

      const data = await response.json()
      console.log("[Study Room] Response data:", data)

      if (!data.success) {
        throw new Error(data.error || "Failed to get response from AI")
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.response || "I received your question but couldn't generate a response.",
        images: data.images || [],
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])

      // Text-to-speech if enabled
      if (enableReadAloud && "speechSynthesis" in window && data.response) {
        const utterance = new SpeechSynthesisUtterance(data.response)
        speechSynthesis.speak(utterance)
      }
    } catch (error) {
      console.error("[Study Room] Error:", error)
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: error instanceof Error 
          ? `❌ Error: ${error.message}\n\nMake sure the Python backend is running:\n1. Open terminal\n2. Run: python api_server.py\n3. Check http://localhost:8080/health`
          : "❌ An unknown error occurred. Please check the console.",
        timestamp: new Date(),
      }
      
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleVoiceInput = (text: string) => {
    setInputValue(text)
  }

  return (
    // FIX 2: Set height to MINIMUM full height and use flex column
    <div className="min-h-full flex flex-col bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      
      {/* Structural Fix: Removed redundant header. Title is now simplified */}
      <div className="max-w-6xl w-full mx-auto px-4 pt-4 pb-0">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">🧠 Study Room</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">Interactive learning with your AI tutor</p>
      </div>

      {/* Chat Area - FIX 2: Use flex-1 to take up all available vertical space, allowing the overflow-y-auto to manage scroll */}
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

      {/* Modern Input Area (Now includes controls and fixed height for alignment) */}
      <div className="border-t border-gray-200 dark:border-slate-700 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl p-4 sticky bottom-0 z-10">
        <div className="max-w-6xl mx-auto space-y-3">
          
          {/* Controls: Mode Selector & Read Aloud (Now in the footer) */}
          <div className="flex items-center justify-between">
            {/* Mode Selector */}
            <div className="flex gap-1 bg-gray-100 dark:bg-slate-800 p-1 rounded-lg">
              {(["text", "voice"] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setInteractionMode(mode)}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
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
              className={`p-2 rounded-lg transition-all text-sm font-medium flex items-center gap-1 ${
                enableReadAloud
                  ? "bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400"
                  : "bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-slate-700"
              }`}
              title={enableReadAloud ? "Read-aloud enabled" : "Read-aloud disabled"}
            >
              🔊 Read Aloud {enableReadAloud ? 'ON' : 'OFF'}
            </button>
          </div>

          {interactionMode === "voice" ? (
            <VoiceInput onInput={handleVoiceInput} onSend={handleSendMessage} />
          ) : (
            <div className="flex items-stretch gap-3">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && !isLoading && handleSendMessage()}
                placeholder="Ask me anything about your materials..."
                disabled={isLoading}
                // FIX 3: Enforce h-12 on input for alignment
                className="flex-1 px-4 py-3 h-12 bg-gray-100 dark:bg-slate-800 border border-gray-300 dark:border-slate-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-all disabled:opacity-50"
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isLoading}
                // FIX 3: Enforce h-12 on button for alignment
                className="h-12 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-400 text-white font-medium rounded-xl transition-all shadow-lg hover:shadow-xl disabled:shadow-none"
              >
                {isLoading ? "..." : "Send"}
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