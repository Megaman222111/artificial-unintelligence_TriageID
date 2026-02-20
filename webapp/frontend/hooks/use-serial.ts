"use client"

import { useState, useCallback, useRef, useEffect } from "react"

const BAUD = 115200
const USER_ID_REGEX = /User ID:\s*"([^"]*)"/

declare global {
  interface Navigator {
    serial?: {
      requestPort: () => Promise<SerialPort>
    }
  }
}

interface SerialPort {
  open: (options: { baudRate: number }) => Promise<void>
  close: () => Promise<void>
  readable: ReadableStream<Uint8Array>
  writable: WritableStream<Uint8Array>
}

export function useSerial(onTagRead: (tagId: string) => void) {
  const [isSupported, setIsSupported] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const onTagReadRef = useRef(onTagRead)
  const portRef = useRef<SerialPort | null>(null)
  const readerRef = useRef<ReadableStreamDefaultReader<Uint8Array> | null>(null)
  const writerRef = useRef<WritableStreamDefaultWriter<Uint8Array> | null>(null)
  const abortRef = useRef(false)

  onTagReadRef.current = onTagRead

  useEffect(() => {
    setIsSupported(typeof navigator !== "undefined" && "serial" in navigator)
  }, [])

  const connect = useCallback(async () => {
    if (typeof navigator === "undefined" || !navigator.serial) {
      setError("Web Serial not supported. Use Chrome or Edge.")
      return
    }
    setError(null)
    abortRef.current = false
    try {
      const port = await navigator.serial.requestPort()
      await port.open({ baudRate: BAUD })
      portRef.current = port
      writerRef.current = port.writable.getWriter()
      const reader = port.readable.getReader()
      readerRef.current = reader
      setIsConnected(true)

      let readBuffer = ""
      const readLoop = async () => {
        try {
          for (;;) {
            if (abortRef.current) break
            const { value, done } = await reader.read()
            if (done) break
            const s = new TextDecoder().decode(value)
            readBuffer += s
            const lines = readBuffer.split(/\r?\n/)
            readBuffer = lines.pop() || ""
            for (const line of lines) {
              const t = line.trim()
              if (!t) continue
              const match = t.match(USER_ID_REGEX)
              if (match) {
                const id = (match[1] || "").trim()
                if (id) onTagReadRef.current(id)
              }
            }
          }
        } catch (e) {
          if (!abortRef.current)
            setError(e instanceof Error ? e.message : "Serial read error")
        } finally {
          reader.releaseLock()
          readerRef.current = null
        }
      }
      readLoop()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Connection failed")
      setIsConnected(false)
    }
  }, [])

  const disconnect = useCallback(async () => {
    abortRef.current = true
    if (readerRef.current) {
      try {
        await readerRef.current.cancel()
      } catch {
        // ignore
      }
      readerRef.current = null
    }
    if (writerRef.current) {
      try {
        await writerRef.current.close()
      } catch {
        // ignore
      }
      writerRef.current = null
    }
    if (portRef.current) {
      try {
        await portRef.current.close()
      } catch {
        // ignore
      }
      portRef.current = null
    }
    setIsConnected(false)
    setError(null)
  }, [])

  useEffect(() => {
    return () => {
      abortRef.current = true
      if (portRef.current) {
        portRef.current.close().catch(() => {})
      }
    }
  }, [])

  return { isSupported, isConnected, error, connect, disconnect }
}
