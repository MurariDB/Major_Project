"use client"

interface NavbarProps {
  currentPage: "dashboard" | "knowledge" | "study"
  setCurrentPage: (page: "dashboard" | "knowledge" | "study") => void
}

export default function Navbar({ currentPage, setCurrentPage }: NavbarProps) {
  return (
    <nav className="bg-(--color-bg-secondary) border-b border-(--color-border) sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-3 cursor-pointer">
            <div className="w-10 h-10 bg-gradient-to-br from-(--color-primary) to-(--color-accent) rounded-xl flex items-center justify-center shadow-lg">
              <span className="text-xl font-bold text-white">⚡</span>
            </div>
            <div>
              <div className="gradient-text font-bold text-lg leading-none">EdgeLearn</div>
              <div className="text-xs text-(--color-text-secondary)">AI Tutor</div>
            </div>
          </div>

          {/* Navigation */}
          <div className="hidden md:flex items-center gap-2">
            {[
              { id: "dashboard", label: "📊 Dashboard", icon: "📊" },
              { id: "knowledge", label: "📚 Library", icon: "📚" },
              { id: "study", label: "🧠 Study", icon: "🧠" },
            ].map((item) => (
              <button
                key={item.id}
                onClick={() => setCurrentPage(item.id as any)}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  currentPage === item.id
                    ? "bg-(--color-primary) text-white shadow-lg"
                    : "text-(--color-text-secondary) hover:bg-(--color-bg-tertiary)"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          {/* Mobile menu */}
          <div className="md:hidden flex items-center gap-1">
            {[
              { id: "dashboard", label: "📊" },
              { id: "knowledge", label: "📚" },
              { id: "study", label: "🧠" },
            ].map((item) => (
              <button
                key={item.id}
                onClick={() => setCurrentPage(item.id as any)}
                className={`p-2 rounded-lg text-xl transition-all ${
                  currentPage === item.id
                    ? "bg-(--color-primary) text-white"
                    : "text-(--color-text-secondary) hover:bg-(--color-bg-tertiary)"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </nav>
  )
}
