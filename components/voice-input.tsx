"use client"

import { useState, useRef } from "react"

interface VoiceInputProps {
  onInput: (text: string) => void
  onSend: () => void
}

export default function VoiceInput({ onInput, onSend }: VoiceInputProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [transcript, setTranscript] = useState("")
  const recognitionRef = useRef<any>(null)

  const startRecording = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognition) {
      alert("Speech Recognition not supported in your browser")
      return
    }

    recognitionRef.current = new SpeechRecognition()
    recognitionRef.current.continuous = true
    recognitionRef.current.interimResults = true
    recognitionRef.current.lang = "en-US"

    recognitionRef.current.onstart = () => setIsRecording(true)
    recognitionRef.current.onend = () => setIsRecording(false)

    recognitionRef.current.onresult = (event: any) => {
      let interimTranscript = ""
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          setTranscript((prev) => prev + " " + transcript)
          onInput(transcript)
        } else {
          interimTranscript += transcript
        }
      }
    }

    recognitionRef.current.start()
  }

  const stopRecording = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex gap-3">
        {!isRecording ? (
          <button onClick={startRecording} className="btn btn-primary flex-1 text-lg py-3">
            🎙️ Start Recording
          </button>
        ) : (
          <>
            <button
              onClick={stopRecording}
              className="btn bg-(--color-warning) text-white flex-1 text-lg py-3 animate-pulse"
            >
              ⏹️ Recording... (Click to stop)
            </button>
          </>
        )}
        {transcript && (
          <button onClick={onSend} className="btn btn-success px-6 text-lg py-3">
            Send →
          </button>
        )}
      </div>
      {transcript && (
        <div className="bg-(--color-bg-tertiary) rounded-lg p-3">
          <p className="text-xs text-(--color-text-secondary) mb-1">Transcript:</p>
          <p className="text-(--color-text-primary) font-medium">{transcript}</p>
        </div>
      )}
    </div>
  )
}
