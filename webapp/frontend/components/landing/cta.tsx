import Link from "next/link"
import { Button } from "@/components/ui/button"

export function CTA() {
  return (
    <section id="about" className="py-24">
      <div className="mx-auto max-w-7xl px-6">
        <div className="rounded-2xl border border-primary/20 bg-primary/5 px-8 py-16 text-center md:px-16">
          <h2 className="text-3xl font-bold tracking-tight font-[family-name:var(--font-heading)] text-foreground md:text-4xl text-balance">
            Built for Healthcare Professionals
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-base leading-relaxed text-muted-foreground">
            MedLink was designed alongside clinicians and emergency responders to address 
            the real-world challenges of patient identification. Our mission is safer, faster 
            care through better technology.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button size="lg" asChild>
              <Link href="/login">
                Provider Login
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="#how-it-works">Learn More</Link>
            </Button>
          </div>
        </div>
      </div>
    </section>
  )
}
