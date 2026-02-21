"use client"

import { useState, useCallback, useEffect, useRef } from "react"
import { Nfc, Usb, UserPlus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import type { Patient } from "@/lib/api"
import { PatientOverlay } from "@/components/dashboard/patient-overlay"
import { scanNfcTag, createPatient } from "@/lib/api"
import { useSerial } from "@/hooks/use-serial"

// Ambient concentric rings config
const AMBIENT_RINGS = [
  { size: "120%", opacity: 0.22, scale: 1.12, duration: 3, delay: 0 },
  { size: "155%", opacity: 0.16, scale: 1.14, duration: 3.4, delay: 0.3 },
  { size: "195%", opacity: 0.11, scale: 1.16, duration: 3.8, delay: 0.6 },
  { size: "240%", opacity: 0.07, scale: 1.18, duration: 4.2, delay: 0.9 },
]

export function NfcScanView() {
  const [scannedPatient, setScannedPatient] = useState<Patient | null>(null)
  const [isScanning, setIsScanning] = useState(false)
  const [scanError, setScanError] = useState<string | null>(null)
  const [emptyCardTagId, setEmptyCardTagId] = useState<string | null>(null)
  const [addPatientOpen, setAddPatientOpen] = useState(false)
  const [addFirstName, setAddFirstName] = useState("")
  const [addLastName, setAddLastName] = useState("")
  const [addRoom, setAddRoom] = useState("")
  const [addNfcIdManual, setAddNfcIdManual] = useState("")
  const [addPatientLoading, setAddPatientLoading] = useState(false)
  const [addPatientError, setAddPatientError] = useState<string | null>(null)
  const [ripples, setRipples] = useState<number[]>([])
  const rippleTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const generateRandomNfcId = useCallback(() => {
    const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    let id = "TI-"
    for (let i = 0; i < 8; i++) id += chars[Math.floor(Math.random() * chars.length)]
    return id
  }, [])

  const nfcIdFromScan = emptyCardTagId != null && emptyCardTagId.trim() !== ""
  const nfcIdForSubmit = nfcIdFromScan ? emptyCardTagId!.trim() : addNfcIdManual.trim()

  const handleTagReadFromSerial = useCallback(async (tagId: string) => {
    setScanError(null)
    setEmptyCardTagId(null)
    setIsScanning(true)
    try {
      const isEmptyCard = tagId.trim() === ""
      if (isEmptyCard) {
        const generatedId = generateRandomNfcId()
        await new Promise((resolve) => setTimeout(resolve, 400))
        setEmptyCardTagId(generatedId)
        setScanError("This card has no ID. A new ID was generated. Add a patient for this card, then use Add/Edit patient to write the ID to the tag.")
        return
      }
      const patient = await scanNfcTag(tagId)
      await new Promise((resolve) => setTimeout(resolve, 400))
      if (patient) setScannedPatient(patient)
      else {
        setScanError(`No patient found for NFC ID "${tagId}".`)
        setEmptyCardTagId(tagId)
      }
    } finally {
      setIsScanning(false)
    }
  }, [generateRandomNfcId])

  const handleOpenAddPatient = useCallback(() => {
    setAddFirstName("")
    setAddLastName("")
    setAddRoom("")
    setAddPatientError(null)
    setAddNfcIdManual(nfcIdFromScan ? "" : (emptyCardTagId ?? ""))
    setAddPatientOpen(true)
  }, [emptyCardTagId, nfcIdFromScan])

  const handleOpenAddPatientManual = useCallback(() => {
    setEmptyCardTagId(null)
    setAddFirstName("")
    setAddLastName("")
    setAddRoom("")
    setAddNfcIdManual("")
    setAddPatientError(null)
    setAddPatientOpen(true)
  }, [])

  const handleSubmitAddPatient = useCallback(async () => {
    if (!nfcIdForSubmit || !addFirstName.trim() || !addLastName.trim()) return
    setAddPatientError(null)
    setAddPatientLoading(true)
    try {
      const patient = await createPatient({
        nfcId: nfcIdForSubmit,
        firstName: addFirstName.trim(),
        lastName: addLastName.trim(),
        room: addRoom.trim() || undefined,
      })
      setAddPatientOpen(false)
      setScanError(null)
      setEmptyCardTagId(null)
      setScannedPatient(patient)
    } catch (err) {
      setAddPatientError(err instanceof Error ? err.message : "Failed to add patient.")
    } finally {
      setAddPatientLoading(false)
    }
  }, [nfcIdForSubmit, addFirstName, addLastName, addRoom])

  const {
    isSupported: serialSupported,
    isConnected: serialConnected,
    error: serialError,
    connect: serialConnect,
    disconnect: serialDisconnect,
  } = useSerial(handleTagReadFromSerial)

  const handleClose = useCallback(() => {
    setScannedPatient(null)
  }, [])

  // Occasional sonar ripple on a random 3-6s interval
  useEffect(() => {
    function scheduleRipple() {
      const delay = 3000 + Math.random() * 3000
      rippleTimerRef.current = setTimeout(() => {
        setRipples((prev) => [...prev, Date.now()])
        scheduleRipple()
      }, delay)
    }
    scheduleRipple()
    return () => {
      if (rippleTimerRef.current) clearTimeout(rippleTimerRef.current)
    }
  }, [])

  // Clean up old ripples after animation ends
  useEffect(() => {
    if (ripples.length === 0) return
    const cleanup = setTimeout(() => {
      setRipples((prev) => prev.slice(1))
    }, 2200)
    return () => clearTimeout(cleanup)
  }, [ripples])

  return (
    <div className="relative flex min-h-[calc(100vh-4rem)] flex-col items-center justify-center overflow-hidden">
      {/* Subtle background glow */}
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute left-1/2 top-1/2 h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary/3 blur-3xl" />
      </div>

      {/* Disconnect only (connect is the main button below) */}
      {serialSupported && serialConnected && (
        <div className="absolute right-4 top-4">
          <Button
            variant="outline"
            size="sm"
            onClick={serialDisconnect}
            className="gap-2 border-primary/30 bg-primary/5 text-primary"
          >
            <Usb className="h-3.5 w-3.5" />
            Disconnect reader
          </Button>
        </div>
      )}

      {/* Status text */}
      <p className="mb-2 text-sm font-medium uppercase tracking-widest text-muted-foreground">
        {isScanning
          ? "Scanning..."
          : serialConnected
            ? "Hold wristband to reader"
            : serialSupported
              ? "Tap the button to connect Arduino"
              : "Web Serial not supported (use Chrome/Edge)"}
      </p>

      <h2 className="mb-10 text-center text-2xl font-bold font-[family-name:var(--font-heading)] text-foreground md:text-3xl text-balance">
        Tap NFC Wristband to Identify Patient
      </h2>

      {/* Scanner button with animated rings behind it */}
      <div className="relative flex items-center justify-center">
        {/* Ambient concentric outlines -- stroke only, no fill */}
        {AMBIENT_RINGS.map((ring, i) => (
          <span
            key={i}
            className="pointer-events-none absolute rounded-full border border-primary"
            style={
              {
                width: ring.size,
                height: ring.size,
                "--ring-opacity": ring.opacity,
                "--ring-scale": ring.scale,
                opacity: ring.opacity,
                filter: "blur(0.5px)",
                animation: `ring-breathe ${ring.duration}s ease-in-out infinite ${ring.delay}s`,
              } as React.CSSProperties
            }
          />
        ))}

        {/* Sonar ripples -- appear randomly, expand outward, fade out */}
        {ripples.map((id) => (
          <span
            key={id}
            className="pointer-events-none absolute rounded-full border-2 border-primary/30"
            style={{
              width: "100%",
              height: "100%",
              animation: "sonar-ripple 2s ease-out forwards",
              filter: "blur(1px)",
            }}
          />
        ))}

        {/* Main button: connect Arduino when disconnected; when connected, scanning is via reader only */}
        <button
          onClick={serialSupported && !serialConnected ? serialConnect : undefined}
          disabled={
            (serialSupported && serialConnected) || isScanning || !!scannedPatient
          }
          className="group relative z-10 flex h-56 w-56 cursor-pointer items-center justify-center rounded-full focus:outline-none disabled:cursor-default disabled:opacity-100 md:h-64 md:w-64"
          aria-label={
            serialConnected
              ? "Waiting for NFC tap on reader"
              : serialSupported
                ? "Connect to Arduino NFC reader"
                : "Web Serial not available"
          }
        >
          {/* Outer glow ring on hover/scan */}
          <div
            className={`absolute inset-0 rounded-full transition-shadow duration-500 ${
              isScanning
                ? "shadow-[0_0_60px_rgba(74,222,128,0.15)]"
                : !serialConnected && serialSupported
                  ? "group-hover:shadow-[0_0_40px_rgba(74,222,128,0.1)]"
                  : serialConnected
                    ? "shadow-[0_0_40px_rgba(74,222,128,0.08)]"
                    : ""
            }`}
          />

          {/* Scanning spinner overlay */}
          {isScanning && (
            <div
              className="absolute inset-0 rounded-full border-2 border-transparent border-t-primary"
              style={{ animation: "scan-spin 1s linear infinite" }}
            />
          )}

          {/* Main circle face */}
          <div
            className={`relative flex h-44 w-44 flex-col items-center justify-center rounded-full border-2 transition-all duration-300 md:h-52 md:w-52 ${
              isScanning
                ? "border-primary bg-primary/10"
                : serialConnected
                  ? "border-primary/40 bg-primary/5"
                  : "border-primary/30 bg-card shadow-lg group-hover:border-primary group-hover:bg-primary/5"
            }`}
          >
            <Nfc
              className={`mb-3 h-12 w-12 transition-colors md:h-14 md:w-14 ${
                isScanning
                  ? "text-primary"
                  : serialConnected
                    ? "text-primary"
                    : "text-primary/60 group-hover:text-primary"
              }`}
            />
            <span
              className={`text-sm font-semibold tracking-wide transition-colors ${
                isScanning
                  ? "text-primary"
                  : serialConnected
                    ? "text-primary"
                    : "text-muted-foreground group-hover:text-foreground"
              }`}
            >
              {isScanning
                ? "Reading..."
                : serialConnected
                  ? "Hold wristband to reader"
                  : serialSupported
                    ? "Connect to Arduino"
                    : "Scan Here"}
            </span>
          </div>
        </button>
      </div>

      {/* Helper text */}
      <p className="mt-10 max-w-xs text-center text-sm leading-relaxed text-muted-foreground">
        Hold the patient&apos;s NFC wristband near this device to retrieve
        their medical records securely.
      </p>

      {(scanError || serialError) && (
        <div className="mt-3 flex flex-col items-center gap-2">
          <p className="text-center text-sm text-destructive">
            {scanError ?? serialError}
          </p>
          {emptyCardTagId !== null && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleOpenAddPatient}
              className="gap-2 border-primary/40 bg-primary/5 text-primary hover:bg-primary/10"
            >
              <UserPlus className="h-4 w-4" />
              {emptyCardTagId.trim() ? "Add patient for this card" : "Add patient (enter ID)"}
            </Button>
          )}
        </div>
      )}

      <div className="mt-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleOpenAddPatientManual}
          className="gap-2 text-muted-foreground hover:text-foreground"
        >
          <UserPlus className="h-4 w-4" />
          Add patient
        </Button>
      </div>

      {/* Add patient dialog (when card is empty or manual add) */}
      <Dialog open={addPatientOpen} onOpenChange={setAddPatientOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>
              {nfcIdFromScan ? "Add patient for this card" : "Add patient"}
            </DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="add-nfc">NFC card ID</Label>
              <Input
                id="add-nfc"
                value={nfcIdFromScan ? (emptyCardTagId ?? "") : addNfcIdManual}
                readOnly={nfcIdFromScan}
                onChange={nfcIdFromScan ? undefined : (e) => setAddNfcIdManual(e.target.value)}
                placeholder={nfcIdFromScan ? undefined : "Enter or scan card ID"}
                className={nfcIdFromScan ? "bg-muted font-mono text-sm" : "font-mono text-sm"}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="add-first">First name</Label>
              <Input
                id="add-first"
                placeholder="First name"
                value={addFirstName}
                onChange={(e) => setAddFirstName(e.target.value)}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="add-last">Last name</Label>
              <Input
                id="add-last"
                placeholder="Last name"
                value={addLastName}
                onChange={(e) => setAddLastName(e.target.value)}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="add-room">Room (optional)</Label>
              <Input
                id="add-room"
                placeholder="e.g. 204"
                value={addRoom}
                onChange={(e) => setAddRoom(e.target.value)}
              />
            </div>
            {addPatientError && (
              <p className="text-sm text-destructive">{addPatientError}</p>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddPatientOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmitAddPatient}
              disabled={
                addPatientLoading ||
                !nfcIdForSubmit ||
                !addFirstName.trim() ||
                !addLastName.trim()
              }
            >
              {addPatientLoading ? "Adding..." : "Add patient"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Patient data overlay */}
      {scannedPatient && (
        <PatientOverlay patient={scannedPatient} onClose={handleClose} />
      )}
    </div>
  )
}
