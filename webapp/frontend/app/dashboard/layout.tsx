"use client"

import { useRouter, usePathname } from "next/navigation"
import { useEffect, useState } from "react"
import { getAccessToken, getMe } from "@/lib/auth"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()
  const [allowed, setAllowed] = useState(false)

  useEffect(() => {
    const token = getAccessToken()
    if (!token) {
      router.replace("/login")
      return
    }
    getMe()
      .then((user) => {
        if (user) setAllowed(true)
        else router.replace("/login")
      })
      .catch(() => router.replace("/login"))
  }, [router, pathname])

  if (!allowed) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-muted-foreground">Checking authentication...</p>
      </div>
    )
  }

  return <>{children}</>
}
