"use client"

import Link from "next/link"
import { Shield, LogOut, Bell } from "lucide-react"
import { Button } from "@/components/ui/button"

export function DashboardShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Top bar */}
      <header className="flex h-16 items-center justify-between border-b border-border bg-card px-6">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <Shield className="h-4 w-4 text-primary-foreground" />
          </div>
          <span className="text-lg font-bold font-[family-name:var(--font-heading)] text-foreground">
            MedLink
          </span>
        </Link>

        <div className="flex items-center gap-4">
          <span className="hidden text-sm text-muted-foreground sm:block">
            Dr. Sarah Mitchell
          </span>
          <Button variant="ghost" size="icon" className="relative">
            <Bell className="h-4 w-4" />
            <span className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full border-2 border-card bg-primary" />
            <span className="sr-only">Notifications</span>
          </Button>
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-sm font-bold text-primary-foreground">
            SM
          </div>
          <Button variant="ghost" size="icon" asChild>
            <Link href="/login">
              <LogOut className="h-4 w-4" />
              <span className="sr-only">Sign out</span>
            </Link>
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
