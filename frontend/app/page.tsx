'use client'

import Link from 'next/link'
import { Bot, Brain, Send, BarChart3, ArrowRight, CheckCircle2, Zap } from 'lucide-react'
import { useEffect, useRef } from 'react'
import { trackPageView, trackMetaPageView } from '@/lib/tracking'

const features = [
  {
    icon: Bot,
    title: 'Lead Sourcing',
    description: 'AI agents automatically find prospects on LinkedIn, web, and inbound channels. Build your pipeline while you sleep.',
    color: 'text-blue-400 bg-blue-400/10',
  },
  {
    icon: Send,
    title: 'Automated Outreach',
    description: 'Personalized email and LinkedIn sequences run on autopilot. Human approval holds ensure you stay in control before any message goes out.',
    color: 'text-purple-400 bg-purple-400/10',
  },
  {
    icon: Brain,
    title: 'Lead Qualification',
    description: 'AI scores and routes leads automatically. Every prospect gets enriched with company data, news, and contact info.',
    color: 'text-emerald-400 bg-emerald-400/10',
  },
  {
    icon: BarChart3,
    title: 'Pipeline Visibility',
    description: 'Real-time dashboard shows every deal, stage, and agent action. Full audit trail so nothing falls through the cracks.',
    color: 'text-orange-400 bg-orange-400/10',
  },
]

const benefits = [
  'AI agents find and qualify leads 24/7',
  'Human-in-the-loop approval queue',
  'LinkedIn + Email + Phone outreach',
  'Full audit trail of every agent action',
  'Open source & self-hosted',
  'Built for sales teams that move fast',
]

const DemoSection = ({ onVisible }: { onVisible: () => void }) => {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!ref.current) return
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          onVisible()
          observer.disconnect()
        }
      },
      { threshold: 0.5 }
    )
    observer.observe(ref.current)
    return () => observer.disconnect()
  }, [onVisible])

  return (
    <section id="demo" className="py-16 bg-secondary/30" ref={ref}>
      <div className="container mx-auto px-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-2xl md:text-3xl font-bold tracking-tight mb-4">See Agentic CRM in Action</h2>
            <p className="text-muted-foreground">Watch how AI agents automate your sales workflow</p>
          </div>
          <div className="aspect-video rounded-xl border border-border bg-card overflow-hidden shadow-2xl">
            <iframe
              src="https://www.loom.com/embed/PLACEHOLDER"
              className="w-full h-full"
              allowFullScreen
              title="Agentic CRM Demo"
            />
          </div>
        </div>
      </div>
    </section>
  )
}

export default function LandingPage() {
  useEffect(() => {
    trackPageView('/', 'Agentic CRM — AI-First CRM Platform')
    trackMetaPageView()
  }, [])
  return (
    <div className="min-h-screen">
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-sm">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <Bot className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="text-lg font-semibold tracking-tight">Agentic CRM</span>
          </div>
          <nav className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Features</a>
            <a href="#demo" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Demo</a>
            <a href="#pricing" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Pricing</a>
            <Link href="/dashboard" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Dashboard</Link>
          </nav>
          <div className="flex items-center gap-4">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
            >
              Get Started
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </header>

      <main>
        <section className="relative overflow-hidden py-24 md:py-32 pt-32">
          <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-transparent to-transparent" />
          <div className="container mx-auto px-6 relative z-10">
            <div className="max-w-4xl mx-auto text-center">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 text-primary text-sm font-medium mb-8">
                <Zap className="h-3.5 w-3.5" />
                AI-first CRM for modern sales teams
              </div>
              <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
                Stop scrolling.
                <br />
                <span className="text-primary">Start sourcing.</span>
              </h1>
              <p className="text-lg md:text-xl text-muted-foreground mb-10 max-w-2xl mx-auto">
                Agentic CRM puts AI agents to work finding leads, qualifying prospects, and managing your pipeline — while you stay in control.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link
                  href="/dashboard"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors"
                >
                  Try the Demo
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <a
                  href="#demo"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-lg border border-border hover:bg-secondary transition-colors"
                >
                  Watch Video
                </a>
              </div>
            </div>
          </div>
        </section>

        <DemoSection onVisible={() => {
          trackPageView('/demo', 'Demo Booking — Agentic CRM')
          trackMetaPageView()
        }} />

        <section id="features" className="py-24">
          <div className="container mx-auto px-6">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">
                AI agents that work while you sleep
              </h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Every feature is designed to automate repetitive work so you can focus on relationships that matter.
              </p>
            </div>
            <div className="grid md:grid-cols-2 gap-6 max-w-5xl mx-auto">
              {features.map((feature) => {
                const Icon = feature.icon
                return (
                  <div
                    key={feature.title}
                    className="p-6 rounded-xl border border-border bg-card hover:border-primary/30 transition-colors"
                  >
                    <div className={`inline-flex items-center justify-center w-12 h-12 rounded-lg ${feature.color} mb-4`}>
                      <Icon className="h-6 w-6" />
                    </div>
                    <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
                    <p className="text-muted-foreground leading-relaxed">
                      {feature.description}
                    </p>
                  </div>
                )
              })}
            </div>
          </div>
        </section>

        <section className="py-24 bg-secondary/30">
          <div className="container mx-auto px-6">
            <div className="max-w-4xl mx-auto">
              <div className="text-center mb-12">
                <h2 className="text-2xl md:text-3xl font-bold tracking-tight mb-4">
                  Built for teams that mean business
                </h2>
                <p className="text-muted-foreground">
                  Everything you need to scale outreach without scaling headcount.
                </p>
              </div>
              <div className="grid sm:grid-cols-2 gap-4">
                {benefits.map((benefit) => (
                  <div key={benefit} className="flex items-center gap-3 p-4 rounded-lg bg-card border border-border">
                    <CheckCircle2 className="h-5 w-5 text-emerald-400 flex-shrink-0" />
                    <span className="text-sm font-medium">{benefit}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="py-16">
          <div className="container mx-auto px-6">
            <div className="max-w-3xl mx-auto text-center">
              <h2 className="text-2xl md:text-3xl font-bold tracking-tight mb-4">
                Ready to let AI do the heavy lifting?
              </h2>
              <p className="text-muted-foreground mb-8">
                Start with the open source version, or talk to us about managed hosting and custom integrations.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link
                  href="/dashboard"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors"
                >
                  Launch Dashboard
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-lg border border-border hover:bg-secondary transition-colors"
                >
                  View on GitHub
                </a>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-border py-12">
        <div className="container mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                <Bot className="h-4 w-4 text-primary-foreground" />
              </div>
              <span className="text-sm font-medium">Agentic CRM</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Open source AI-first CRM. Built for teams that move fast.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}