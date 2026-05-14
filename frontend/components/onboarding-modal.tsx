'use client'

import { useOnboarding } from '@/lib/onboarding-context'
import { ONBOARDING_STEPS } from '@/lib/onboarding-steps'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { X, Rocket, Check } from 'lucide-react'
import { useRouter } from 'next/navigation'

export default function OnboardingModal() {
  const { currentStep, skipOnboarding, nextStep, completedSteps } = useOnboarding()
  const router = useRouter()

  if (!currentStep) return null

  const currentIndex = ONBOARDING_STEPS.findIndex(s => s.id === currentStep.id)
  const totalSteps = ONBOARDING_STEPS.length

  const handleAction = () => {
    if (currentStep.page) {
      router.push(currentStep.page)
    }
    nextStep()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="absolute inset-0" onClick={skipOnboarding} />
      <Card className="w-full max-w-lg mx-4 shadow-2xl border-primary/20 animate-scale-in">
        <CardHeader className="relative pb-4">
          <button
            onClick={skipOnboarding}
            className="absolute right-4 top-4 p-1 rounded-lg hover:bg-secondary transition-colors"
          >
            <X className="h-4 w-4 text-muted-foreground" />
          </button>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
              <Rocket className="h-5 w-5 text-primary" />
            </div>
            <div>
              <Badge variant="secondary" className="font-mono text-xs mb-1">
                Step {currentIndex + 1} of {totalSteps}
              </Badge>
              <CardTitle className="text-xl">{currentStep.title}</CardTitle>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <p className="text-muted-foreground leading-relaxed">
            {currentStep.description}
          </p>

          <div className="flex gap-1.5">
            {ONBOARDING_STEPS.map((step, idx) => (
              <div
                key={step.id}
                className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${
                  idx < currentIndex ? 'bg-primary' :
                  idx === currentIndex ? 'bg-primary/50' :
                  'bg-secondary'
                }`}
              />
            ))}
          </div>

          <div className="flex items-center justify-between pt-2">
            <div className="flex gap-1">
              {completedSteps.map(stepId => (
                <Check key={stepId} className="h-4 w-4 text-primary" />
              ))}
            </div>
            <div className="flex gap-2">
              <Button variant="ghost" onClick={skipOnboarding}>
                Skip Tour
              </Button>
              <Button onClick={handleAction}>
                {currentStep.action}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}