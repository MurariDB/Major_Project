import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { message } = body
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8080"

    const response = await fetch(`${backendUrl}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    })

    if (!response.ok) throw new Error(`Backend returned ${response.status}`)

    const data = await response.json()
    
    // Convert local file paths to backend URLs
    if (data.images && Array.isArray(data.images)) {
      data.images = data.images.map((path: string) => {
        const match = path.match(/([^/]+)\/page_(\d+)\/([^/]+)$/)
        if (match) {
          const [, pdfName, pageNum, filename] = match
          return `${backendUrl}/api/images/${pdfName}/page_${pageNum}/${filename}`
        }
        return path
      })
    }

    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Failed", success: false },
      { status: 500 }
    )
  }
}