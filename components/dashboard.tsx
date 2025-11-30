"use client"

import { useState, useEffect } from "react"
import StatCard from "./stat-card"
import QuickActionCard from "./quick-action-card"

interface DashboardProps {
  setCurrentPage: (page: "dashboard" | "knowledge" | "study") => void
}

export default function Dashboard({ setCurrentPage }: DashboardProps) {
  const [studyStreak, setStudyStreak] = useState(3)
  const [sessionTime, setSessionTime] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setSessionTime((prev) => prev + 1)
    }, 60000) // Update every minute
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="space-y-8 animate-fadeInUp">
      {/* Welcome Header */}
      <div className="space-y-2">
        <h1 className="gradient-text text-4xl md:text-5xl font-bold">Welcome back, learner.</h1>
        <p className="text-(--color-text-secondary) text-lg">
          Your offline AI tutor is ready to help you master any topic.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          title="Study Streak"
          value={`${studyStreak}`}
          subtitle="Days"
          icon="🔥"
          trend="+1 today"
          trendColor="success"
        />
        <StatCard
          title="Materials"
          value="0"
          subtitle="Documents"
          icon="📄"
          trend="Ready to upload"
          trendColor="primary"
        />
        <StatCard
          title="Session Time"
          value={`${sessionTime}`}
          subtitle="Minutes"
          icon="⏱️"
          trend="Active now"
          trendColor="success"
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <QuickActionCard
          title="Upload Course Materials"
          description="Add PDFs and lecture notes to build your knowledge base"
          icon="📂"
          buttonText="Go to Library"
          buttonColor="primary"
          onClick={() => setCurrentPage("knowledge")}
          gradient="from-blue-400 to-blue-600"
        />
        <QuickActionCard
          title="Start Studying"
          description="Ask questions about your materials using voice or text"
          icon="🧠"
          buttonText="Enter Study Room"
          buttonColor="success"
          onClick={() => setCurrentPage("study")}
          gradient="from-green-400 to-green-600"
        />
      </div>

      {/* Tips Section */}
      <div className="bg-gradient-to-r from-(--color-primary)/10 to-(--color-accent)/10 rounded-xl p-6 border border-(--color-primary)/20">
        <h3 className="font-serif font-bold text-lg text-(--color-text-primary) mb-3">💡 Pro Tips</h3>
        <ul className="space-y-2 text-(--color-text-secondary)">
          <li>• Upload multiple PDFs at once to build a comprehensive knowledge base</li>
          <li>• Use voice input for hands-free learning during breaks</li>
          <li>• Zoom in on diagrams to study them in detail</li>
          <li>• Enable read-aloud to have responses read to you</li>
        </ul>
      </div>
    </div>
  )
}
