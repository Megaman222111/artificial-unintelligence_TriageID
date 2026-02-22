"use client"

import { useEffect } from "react"
import { usePathname } from "next/navigation"
import { useSerialContext } from "@/contexts/serial-context"

/**
 * When the user is on /dashboard, ensure the NFC reader is in READ mode
 * (e.g. after returning from the edit page where it may have been in WRITE mode).
 */
export function DashboardReadModeReset() {
  const pathname = usePathname()
  const { send } = useSerialContext()

  useEffect(() => {
    if (pathname === "/dashboard") {
      send("READ").catch(() => {})
    }
  }, [pathname, send])

  return null
}
