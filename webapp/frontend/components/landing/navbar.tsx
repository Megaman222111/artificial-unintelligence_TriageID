"use client"

import Link from "next/link"
import { useState } from "react"
import { Menu, X, Shield } from "lucide-react"
import { Button } from "@/components/ui/button"

export function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
            <Shield className="h-5 w-5 text-primary-foreground" />
          </div>
          <span className="text-xl font-bold tracking-tight font-[family-name:var(--font-heading)] text-foreground">
            MedLink
          </span>
        </Link>

        <div className="hidden items-center gap-8 md:flex">
          <Link href="/" className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
            Home
          </Link>
          <Link href="#features" className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
            Features
          </Link>
          <Link href="#how-it-works" className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
            How It Works
          </Link>
          <Link href="#about" className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
            About
          </Link>
        </div>

        <div className="hidden items-center gap-3 md:flex">
          <Button asChild>
            <Link href="/login">Provider Login</Link>
          </Button>
        </div>

        <button
          className="md:hidden"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </nav>

      {mobileOpen && (
        <div className="border-t border-border bg-background px-6 pb-6 md:hidden">
          <div className="flex flex-col gap-4 pt-4">
            <Link href="/" className="text-sm font-medium text-muted-foreground" onClick={() => setMobileOpen(false)}>
              Home
            </Link>
            <Link href="#features" className="text-sm font-medium text-muted-foreground" onClick={() => setMobileOpen(false)}>
              Features
            </Link>
            <Link href="#how-it-works" className="text-sm font-medium text-muted-foreground" onClick={() => setMobileOpen(false)}>
              How It Works
            </Link>
            <Link href="#about" className="text-sm font-medium text-muted-foreground" onClick={() => setMobileOpen(false)}>
              About
            </Link>
            <div className="pt-2">
              <Button asChild className="w-full">
                <Link href="/login">Provider Login</Link>
              </Button>
            </div>
          </div>
        </div>
      )}
    </header>
  )
}
