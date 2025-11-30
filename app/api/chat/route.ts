import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { message } = body

    // Connect to Python backend on port 8080
    const response = await fetch("http://127.0.0.1:8080/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    })

    if (!response.ok) {
      console.error(`Backend Error: ${response.status}`)
      return NextResponse.json(
        { error: `Backend refused connection (${response.status})`, success: false }, 
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
    
  } catch (error) {
    console.error("Connection Failed:", error)
    return NextResponse.json(
      { error: "Could not connect to Python backend. Is it running on port 8080?", success: false }, 
      { status: 500 }
    )
  }
}