'use client'

import { useOnboarding } from '@/lib/onboarding-context'
import { ONBOARDING_STEPS } from '@/lib/onboarding-steps'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Rocket, CheckCircle, Circle } from 'lucide-react'

export default function OnboardingProgress() {
  const { isComplete, completedSteps, startOnboarding } = useOnboarding()

  const progress = (completedSteps.length / ONBOARDING_STEPS.length) * 100

  if (isComplete) {
    return (
      <Card className="border-emerald-500/20 bg-emerald-500/5">
        <CardContent className="flex items-center justify-between py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
              <CheckCircle className="h-5 w-5 text-emerald-400" />
            </div>
            <div>
              <p className="font-medium text-sm">Onboarding Complete!</p>
              <p className="text-xs text-muted-foreground">You&apos;re ready to use Agentic CRM</p>
            </div>
          </div>
          <Badge variant="default" className="bg-emerald-500/20 text-emerald-400 border-emerald-500/20">
            Ready
          </Badge>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-primary/20">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Rocket className="h-4 w-4 text-primary" />
          Getting Started
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Progress</span>
            <span className="font-mono text-xs">{completedSteps.length}/{ONBOARDING_STEPS.length}</span>
          </div>
          <div className="h-2 rounded-full bg-secondary overflow-hidden">
            <div
              className="h-full rounded-full bg-primary transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <div className="space-y-2">
          {ONBOARDING_STEPS.map((step, idx) => {
            const isCompleted = completedSteps.includes(step.id)
            const isCurrent = !isCompleted && (idx === completedSteps.length)
            return (
              <div
                key={step.id}
                className={`flex items-center gap-3 p-2 rounded-lg transition-colors ${
                  isCurrent ? 'bg-primary/5 border border-primary/20' :
                  isCompleted ? 'opacity-60' : ''
                }`}
              >
                {isCompleted ? (
                  <CheckCircle className="h-4 w-4 text-primary flex-shrink-0" />
                ) : isCurrent ? (
                  <Circle className="h-4 w-4 text-primary flex-shrink-0 animate-pulse" />
                ) : (
                  <Circle className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                )}
                <span className={`text-sm ${isCompleted ? 'text-muted-foreground line-through' : ''}`}>
                  {step.title}
                </span>
              </div>
            )
          })}
        </div>

        <Button variant="outline" size="sm" className="w-full" onClick={startOnboarding}>
          Resume Tour
        </Button>
      </CardContent>
    </Card>
  )
}