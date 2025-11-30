interface DocumentListProps {
  documents: string[]
}

export default function DocumentList({ documents }: DocumentListProps) {
  return (
    <div className="space-y-2">
      {documents.map((doc, idx) => (
        <div
          key={idx}
          className="flex items-center justify-between p-4 bg-(--color-bg-tertiary) rounded-lg hover:bg-(--color-border) transition-colors"
        >
          <div className="flex items-center gap-3">
            <span className="text-2xl">📄</span>
            <div className="flex-1">
              <p className="font-medium text-(--color-text-primary) truncate">{doc}</p>
              <p className="text-xs text-(--color-text-tertiary)">Ready to process</p>
            </div>
          </div>
          <button className="text-(--color-text-tertiary) hover:text-(--color-accent) text-xl">✕</button>
        </div>
      ))}
    </div>
  )
}
