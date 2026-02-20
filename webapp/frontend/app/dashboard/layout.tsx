"use client"

import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { getAccessToken } from "@/lib/auth"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const [allowed, setAllowed] = useState<boolean | null>(null)

  useEffect(() => {
    const token = getAccessToken()
    if (!token) {
      router.replace("/login")
      return
    }
    setAllowed(true)
  }, [router])

  if (allowed === null) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-muted-foreground">Checking authentication...</p>
      </div>
    )
  }

  if (!allowed) {
    return null
  }

  return <>{children}</>
}
