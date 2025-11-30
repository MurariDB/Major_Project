interface StatCardProps {
  title: string
  value: string
  subtitle: string
  icon: string
  trend?: string
  trendColor?: "primary" | "success" | "warning"
}

const trendColorMap = {
  primary: "text-(--color-primary)",
  success: "text-(--color-success)",
  warning: "text-(--color-warning)",
}

export default function StatCard({ title, value, subtitle, icon, trend, trendColor = "primary" }: StatCardProps) {
  return (
    <div className="card hover:shadow-lg group">
      <div className="flex items-start justify-between mb-4">
        <div className="text-4xl group-hover:scale-110 transition-transform">{icon}</div>
        {trend && <span className={`text-sm font-medium badge badge-primary`}>{trend}</span>}
      </div>
      <p className="text-(--color-text-secondary) text-sm mb-1">{title}</p>
      <div className="flex items-baseline gap-2">
        <span className="text-4xl font-bold gradient-text">{value}</span>
        <span className="text-(--color-text-tertiary) text-sm">{subtitle}</span>
      </div>
    </div>
  )
}
