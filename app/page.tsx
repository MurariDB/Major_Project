"use client"

import { useState, useEffect } from "react"
import Navbar from "@/components/navbar"
import Dashboard from "@/components/dashboard"
import KnowledgeBase from "@/components/knowledge-base"
import StudyRoom from "@/components/study-room"

export default function Home() {
  const [currentPage, setCurrentPage] = useState<"dashboard" | "knowledge" | "study">("dashboard")
  const [isInitialized, setIsInitialized] = useState(false)

  useEffect(() => {
    // Simulate initialization
    const timer = setTimeout(() => setIsInitialized(true), 1500)
    return () => clearTimeout(timer)
  }, [])

  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-(--color-primary) via-(--color-bg-primary) to-(--color-accent-light) flex items-center justify-center">
        <div className="text-center">
          <div className="w-20 h-20 bg-gradient-to-br from-(--color-primary) to-(--color-accent) rounded-2xl flex items-center justify-center mx-auto mb-6 animate-pulse-scale shadow-lg">
            <span className="text-4xl">⚡</span>
          </div>
          <h1 className="gradient-text text-4xl font-bold mb-2">EdgeLearn</h1>
          <p className="text-(--color-text-secondary) mb-8">Initializing your AI tutor...</p>
          <div className="flex gap-1 justify-center">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="w-2 h-2 rounded-full bg-(--color-primary) animate-pulse"
                style={{ animationDelay: `${i * 150}ms` }}
              />
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-(--color-bg-primary)">
      <Navbar currentPage={currentPage} setCurrentPage={setCurrentPage} />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentPage === "dashboard" && <Dashboard setCurrentPage={setCurrentPage} />}
        {currentPage === "knowledge" && <KnowledgeBase />}
        {currentPage === "study" && <StudyRoom />}
      </main>
    </div>
  )
}
