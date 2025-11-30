import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { transcription } = body

    const backendUrl = process.env.BACKEND_URL || "http://localhost:8080"

    console.log("[v0] Sending voice query to backend:", transcription)

    const response = await fetch(`${backendUrl}/api/voice`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ transcription }),
    })

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("[v0] Voice error:", error)
    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : "Failed to process voice",
        success: false,
      },
      { status: 500 },
    )
  }
}
