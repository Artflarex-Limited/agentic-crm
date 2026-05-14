'use client'

import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import { ONBOARDING_STEPS, ONBOARDING_STORAGE_KEY, type OnboardingStep } from './onboarding-steps'

interface OnboardingContextValue {
  currentStep: OnboardingStep | null
  isComplete: boolean
  completedSteps: string[]
  startOnboarding: () => void
  completeStep: (stepId: string) => void
  skipOnboarding: () => void
  nextStep: () => void
}

const OnboardingContext = createContext<OnboardingContextValue | null>(null)

export function OnboardingProvider({ children }: { children: ReactNode }) {
  const [completedSteps, setCompletedSteps] = useState<string[]>([])
  const [isComplete, setIsComplete] = useState(false)
  const [showOnboarding, setShowOnboarding] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem(ONBOARDING_STORAGE_KEY)
    if (stored) {
      const data = JSON.parse(stored)
      setCompletedSteps(data.completedSteps || [])
      setIsComplete(data.isComplete || false)
      setShowOnboarding(false)
    } else {
      setShowOnboarding(true)
    }
  }, [])

  const startOnboarding = () => {
    setShowOnboarding(true)
  }

  const completeStep = (stepId: string) => {
    const newCompleted = [...completedSteps, stepId]
    setCompletedSteps(newCompleted)

    const currentIndex = ONBOARDING_STEPS.findIndex(s => s.id === stepId)
    if (currentIndex < ONBOARDING_STEPS.length - 1) {
      // More steps to go
    } else {
      // All steps complete
      setIsComplete(true)
      localStorage.setItem(ONBOARDING_STORAGE_KEY, JSON.stringify({
        completedSteps: newCompleted,
        isComplete: true,
      }))
    }
  }

  const skipOnboarding = () => {
    setShowOnboarding(false)
    setIsComplete(true)
    localStorage.setItem(ONBOARDING_STORAGE_KEY, JSON.stringify({
      completedSteps: ONBOARDING_STEPS.map(s => s.id),
      isComplete: true,
    }))
  }

  const nextStep = () => {
    const allSteps = [...completedSteps]
    const currentStep = ONBOARDING_STEPS.find(s => !completedSteps.includes(s.id))
    if (currentStep) {
      completeStep(currentStep.id)
    }
  }

  const currentStep = ONBOARDING_STEPS.find(s => !completedSteps.includes(s.id)) || null

  return (
    <OnboardingContext.Provider value={{
      currentStep: showOnboarding && !isComplete ? currentStep : null,
      isComplete,
      completedSteps,
      startOnboarding,
      completeStep,
      skipOnboarding,
      nextStep,
    }}>
      {children}
    </OnboardingContext.Provider>
  )
}

export function useOnboarding() {
  const context = useContext(OnboardingContext)
  if (!context) {
    throw new Error('useOnboarding must be used within OnboardingProvider')
  }
  return context
}