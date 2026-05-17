'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { LayoutDashboard, Users, Bot, Settings, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import { OnboardingProvider } from '@/lib/onboarding-context'
import OnboardingModal from '@/components/onboarding-modal'
import OnboardingProgress from '@/components/onboarding-progress'
import { Providers } from '@/lib/providers'

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/leads', label: 'Leads', icon: Users },
  { href: '/agents', label: 'Agents', icon: Bot },
  { href: '/settings', label: 'Settings', icon: Settings },
]

function Sidebar() {
  const pathname = usePathname()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  return (
    <aside className={cn(
      'border-r border-border bg-bg-muted flex flex-col shrink-0 transition-all duration-200',
      sidebarCollapsed ? 'w-16' : 'w-64'
    )}>
      <div className={cn(
        'h-16 border-b border-border px-4 flex items-center gap-3',
        sidebarCollapsed && 'justify-center'
      )}>
        <div className={cn(
          'flex items-center gap-3',
          sidebarCollapsed && 'flex-col'
        )}>
          <div className="bg-accent/10 border border-accent/20 rounded-[var(--radius-md)] w-8 h-8 flex items-center justify-center shrink-0">
            <Bot className="text-accent h-4 w-4" />
          </div>
          {!sidebarCollapsed && <h1 className="text-lg font-semibold tracking-tight whitespace-nowrap">Agentic CRM</h1>}
        </div>
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className={cn(
            'ml-auto p-1 rounded hover:bg-surface transition-colors',
            sidebarCollapsed && 'absolute right-2'
          )}
        >
          <ChevronRight className={cn('h-4 w-4 text-text-muted transition-transform duration-200', !sidebarCollapsed && 'rotate-180')} />
        </button>
      </div>
      <nav className="flex-1 p-4">
        <div className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href))
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-[var(--radius-md)] px-3 py-2.5 text-sm font-medium transition-all duration-150 group',
                  isActive
                    ? 'bg-accent/10 text-accent border-l-2 border-accent ml-0 pl-[10px]'
                    : 'text-text-muted hover:bg-surface hover:text-text-secondary'
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {!sidebarCollapsed && item.label}
              </Link>
            )
          })}
        </div>
      </nav>
      <div className="p-4 border-t border-border">
        {!sidebarCollapsed && <OnboardingProgress />}
      </div>
    </aside>
  )
}

function RootLayoutClient({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  return (
    <OnboardingProvider>
      <Providers
        ga4MeasurementId={process.env.NEXT_PUBLIC_GA4_MEASUREMENT_ID}
        hubspotPortalId={process.env.NEXT_PUBLIC_HUBSPOT_PORTAL_ID}
      >
        <div className="flex min-h-screen bg-background">
          <Sidebar />
          <main className="flex-1 flex flex-col">
            <header className="h-14 border-b border-border/50 bg-bg-base/80 backdrop-blur-md sticky top-0 z-10">
              <div className="flex items-center justify-between h-full px-6">
                {/* Left: Page title */}
                <div className="flex items-center gap-3">
                  <h2 className="text-base font-semibold font-display tracking-tight text-text-primary">
                    {navItems.find(item => pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href)))?.label || 'Dashboard'}
                  </h2>
                  {/* Live indicator */}
                  <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                    <span className="relative flex h-1.5 w-1.5">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-400"></span>
                    </span>
                    <span className="text-xs text-emerald-400 font-medium">Live</span>
                  </div>
                </div>

                {/* Right: Search + Avatar */}
                <div className="flex items-center gap-3">
                  {/* Search */}
                  <div className="relative">
                    <input
                      type="text"
                      placeholder="Search... ⌘K"
                      className="w-64 h-9 rounded-[var(--radius-md)] border border-border bg-surface pl-9 pr-3 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-all"
                    />
                    <svg className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>

                  {/* Notification bell */}
                  <button className="relative w-8 h-8 rounded-[var(--radius-md)] bg-surface border border-border flex items-center justify-center text-text-muted hover:text-text-primary hover:border-border-hover transition-colors">
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2 2 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                    </svg>
                    {/* Notification dot */}
                    <span className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-accent" />
                  </button>

                  {/* Avatar */}
                  <div className="w-8 h-8 rounded-[var(--radius-md)] bg-accent/10 border border-accent/20 flex items-center justify-center">
                    <span className="text-xs font-semibold text-accent">A</span>
                  </div>
                </div>
              </div>
            </header>
            <div className="flex-1 p-6 overflow-auto">
              {children}
            </div>
          </main>
          <OnboardingModal />
        </div>
      </Providers>
    </OnboardingProvider>
  )
}

export default RootLayoutClient