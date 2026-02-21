"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { Shield, LogOut } from "lucide-react"
import { Button } from "@/components/ui/button"
import { getMe, logout as authLogout, type AuthUser } from "@/lib/auth"

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [user, setUser] = useState<AuthUser | null>(null)

  useEffect(() => {
    getMe().then((u) => setUser(u))
  }, [])

  function handleLogout() {
    authLogout()
    router.push("/login")
    router.refresh()
  }

  return (
    <div className="flex min-h-screen flex-col">
      {/* Top bar */}
      <header className="flex h-16 items-center justify-between border-b border-border bg-card px-6">
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <Shield className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="text-lg font-bold font-[family-name:var(--font-heading)] text-foreground">
              TriageID
            </span>
          </Link>
          <Link
            href="/dashboard/patients/edit"
            className="text-sm font-medium text-muted-foreground hover:text-foreground"
          >
            Add/Edit patient info
          </Link>
        </div>

        <div className="flex items-center gap-4">
          {user && (
            <span className="hidden text-sm text-muted-foreground sm:block">
              {[user.firstName, user.lastName].filter(Boolean).join(" ") || user.email}
            </span>
          )}
          <Button variant="ghost" size="icon" onClick={handleLogout}>
            <LogOut className="h-4 w-4" />
            <span className="sr-only">Sign out</span>
          </Button>
        </div>
      </header>

      {/* Page content */}
      <main className="flex-1 bg-background">
        {children}
      </main>
    </div>
  )
}
