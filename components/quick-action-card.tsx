"use client"

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
          className={`btn ${buttonColor === "primary" ? "btn-primary" : "btn-success"} bg-white text-(--color-text-primary) hover:bg-gray-100 font-semibold`}
        >
          {buttonText}
          <span>→</span>
        </button>
      </div>
    </div>
  )
}
