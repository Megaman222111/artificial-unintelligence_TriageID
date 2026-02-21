"use client"

import { createContext, useCallback, useContext, useRef, useState, useEffect } from "react"

const BAUD = 115200
// Arduino menu mode: "User ID: \"...\""; command mode: "OK|READ|userid"
const USER_ID_REGEX = /User ID:\s*"([^"]*)"/
const OK_READ_REGEX = /^OK\|READ\|(.+)$/
const SERIAL_FILTER_COOKIE = "triageid_serial_filter"
const COOKIE_MAX_AGE_DAYS = 365

interface SerialPortFilter {
  usbVendorId: number
  usbProductId: number
}

declare global {
  interface Navigator {
    serial?: {
      requestPort: (options?: { filters?: SerialPortFilter[] }) => Promise<SerialPort>
      getPorts: () => Promise<SerialPort[]>
    }
  }
}

interface SerialPort {
  open: (options: { baudRate: number }) => Promise<void>
  close: () => Promise<void>
  getInfo: () => { usbVendorId?: number; usbProductId?: number }
  readable: ReadableStream<Uint8Array>
  writable: WritableStream<Uint8Array>
}

function getSerialFilterFromCookie(): SerialPortFilter | null {
  if (typeof document === "undefined") return null
  const match = document.cookie.match(new RegExp(`(?:^|; )\\s*${SERIAL_FILTER_COOKIE}=([^;]*)`))
  if (!match) return null
  try {
    const parsed = JSON.parse(decodeURIComponent(match[1])) as SerialPortFilter
    if (typeof parsed?.usbVendorId === "number" && typeof parsed?.usbProductId === "number") return parsed
  } catch {
    // ignore
  }
  return null
}

function setSerialFilterCookie(filter: SerialPortFilter): void {
  if (typeof document === "undefined") return
  const value = encodeURIComponent(JSON.stringify(filter))
  const maxAge = COOKIE_MAX_AGE_DAYS * 24 * 60 * 60
  document.cookie = `${SERIAL_FILTER_COOKIE}=${value}; path=/; max-age=${maxAge}; SameSite=Lax`
}

function clearSerialFilterCookie(): void {
  if (typeof document === "undefined") return
  document.cookie = `${SERIAL_FILTER_COOKIE}=; path=/; max-age=0`
}

export interface SerialContextValue {
  isSupported: boolean
  isConnected: boolean
  isReconnecting: boolean
  error: string | null
  connect: () => Promise<void>
  disconnect: () => Promise<void>
  send: (text: string) => Promise<void>
  setOnTagRead: (callback: ((tagId: string) => void) | null) => void
}

const SerialContext = createContext<SerialContextValue | null>(null)

export function SerialProvider({ children }: { children: React.ReactNode }) {
  const [isSupported, setIsSupported] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [isReconnecting, setIsReconnecting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const onTagReadRef = useRef<((tagId: string) => void) | null>(null)
  const portRef = useRef<SerialPort | null>(null)
  const readerRef = useRef<ReadableStreamDefaultReader<Uint8Array> | null>(null)
  const writerRef = useRef<WritableStreamDefaultWriter<Uint8Array> | null>(null)
  const abortRef = useRef(false)

  const setOnTagRead = useCallback((callback: ((tagId: string) => void) | null) => {
    onTagReadRef.current = callback
  }, [])

  useEffect(() => {
    setIsSupported(typeof navigator !== "undefined" && "serial" in navigator)
  }, [])

  const openPortAndRead = useCallback((port: SerialPort) => {
    portRef.current = port
    writerRef.current = port.writable.getWriter()
    const reader = port.readable.getReader()
    readerRef.current = reader
    setIsConnected(true)
    setError(null)

    const info = port.getInfo?.()
    if (info?.usbVendorId != null && info?.usbProductId != null) {
      setSerialFilterCookie({
        usbVendorId: info.usbVendorId,
        usbProductId: info.usbProductId,
      })
    }

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
            let id: string | null = null
            const userMatch = t.match(USER_ID_REGEX)
            if (userMatch) id = (userMatch[1] ?? "").trim()
            else {
              const okMatch = t.match(OK_READ_REGEX)
              if (okMatch) id = (okMatch[1] ?? "").trim()
            }
            if (id != null && id !== "") onTagReadRef.current?.(id)
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
  }, [])

  const connect = useCallback(async () => {
    if (typeof navigator === "undefined" || !navigator.serial) {
      setError("Web Serial not supported. Use Chrome or Edge.")
      return
    }
    setError(null)
    abortRef.current = false
    const savedFilter = getSerialFilterFromCookie()
    try {
      const port = await navigator.serial.requestPort(
        savedFilter ? { filters: [savedFilter] } : undefined
      )
      await port.open({ baudRate: BAUD })
      openPortAndRead(port)
    } catch (e) {
      clearSerialFilterCookie()
      setError(e instanceof Error ? e.message : "Connection failed")
      setIsConnected(false)
    }
  }, [openPortAndRead])

  useEffect(() => {
    if (typeof navigator === "undefined" || !navigator.serial) return
    const savedFilter = getSerialFilterFromCookie()
    if (!savedFilter) return

    let cancelled = false
    setIsReconnecting(true)
    navigator.serial
      .getPorts()
      .then((ports) => {
        if (cancelled) return
        for (const port of ports) {
          const info = port.getInfo?.()
          if (
            info?.usbVendorId === savedFilter.usbVendorId &&
            info?.usbProductId === savedFilter.usbProductId
          ) {
            return port
              .open({ baudRate: BAUD })
              .then(() => {
                if (!cancelled) {
                  abortRef.current = false
                  openPortAndRead(port)
                }
              })
              .catch(() => {
                clearSerialFilterCookie()
              })
              .finally(() => {
                if (!cancelled) setIsReconnecting(false)
              })
          }
        }
        setIsReconnecting(false)
      })
      .catch(() => {
        setIsReconnecting(false)
      })

    return () => {
      cancelled = true
      setIsReconnecting(false)
    }
  }, [openPortAndRead])

  const send = useCallback(async (text: string) => {
    if (!writerRef.current) return
    const data = new TextEncoder().encode(text.endsWith("\n") ? text : text + "\n")
    await writerRef.current.write(data)
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

  const value: SerialContextValue = {
    isSupported,
    isConnected,
    isReconnecting,
    error,
    connect,
    disconnect,
    send,
    setOnTagRead,
  }

  return (
    <SerialContext.Provider value={value}>
      {children}
    </SerialContext.Provider>
  )
}

export function useSerialContext(): SerialContextValue {
  const ctx = useContext(SerialContext)
  if (!ctx) {
    return {
      isSupported: false,
      isConnected: false,
      isReconnecting: false,
      error: null,
      connect: async () => {},
      disconnect: async () => {},
      send: async () => {},
      setOnTagRead: () => {},
    }
  }
  return ctx
}
