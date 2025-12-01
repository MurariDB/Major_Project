// components/quick-action-card.tsx

"use client"

import { cn } from '@/lib/utils' // Assuming you have a cn utility for class merging

interface QuickActionCardProps {
  title: string
  description: string
  icon: string
  buttonText: string
  buttonColor: "primary" | "success"
  onClick: () => void
  gradient: string
}

export default function QuickActionCard({
  title,
  description,
  icon,
  buttonText,
  buttonColor,
  onClick,
  gradient,
}: QuickActionCardProps) {

  // Dynamically set button classes based on the desired color scheme
  const buttonClass = cn(
    "py-2 px-4 rounded-lg font-bold transition-all",
    // Base style: white text, background from the gradient prop
    "bg-white text-gray-800 hover:bg-gray-100", // Using explicit gray to stand out against white card

    // Custom coloring for the text and hover state inside the gradient
    buttonColor === "primary" && "text-blue-600 hover:text-blue-800",
    buttonColor === "success" && "text-green-600 hover:text-green-800",
  );

  return (
    <div
      className={`bg-gradient-to-br ${gradient} rounded-xl p-8 text-white relative overflow-hidden group cursor-pointer hover:shadow-xl transition-shadow`}
    >
      {/* Background decoration */}
      <div className="absolute -right-20 -top-20 w-40 h-40 bg-white/10 rounded-full group-hover:scale-110 transition-transform" />

      <div className="relative z-10">
        <div className="text-5xl mb-4 inline-block">{icon}</div>
        <h3 className="font-serif font-bold text-2xl mb-2">{title}</h3>
        <p className="text-white/90 mb-6 text-sm leading-relaxed">{description}</p>
        <button
          onClick={onClick}
          className={cn(
            "inline-flex items-center justify-center gap-2", // Added flex utilities for icon alignment
            buttonClass
          )}
        >
          {buttonText}
          <span className="text-xl">→</span>
        </button>
      </div>
    </div>
  )
}