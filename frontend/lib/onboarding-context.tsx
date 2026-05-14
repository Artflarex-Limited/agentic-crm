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
  isTourActive: boolean
  tourTarget: string | null
  advanceTour: (targetSelector?: string) => void
}

const OnboardingContext = createContext<OnboardingContextValue | null>(null)

export function OnboardingProvider({ children }: { children: ReactNode }) {
  const [completedSteps, setCompletedSteps] = useState<string[]>([])
  const [isComplete, setIsComplete] = useState(false)
  const [showOnboarding, setShowOnboarding] = useState(false)
  const [isTourActive, setIsTourActive] = useState(false)
  const [tourStepIndex, setTourStepIndex] = useState(0)

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
    setCompletedSteps([])
    setIsComplete(false)
    setTourStepIndex(0)
    setShowOnboarding(true)
    setIsTourActive(true)
  }

  const completeStep = (stepId: string) => {
    const newCompleted = [...completedSteps, stepId]
    setCompletedSteps(newCompleted)

    const currentIndex = ONBOARDING_STEPS.findIndex(s => s.id === stepId)
    if (currentIndex < ONBOARDING_STEPS.length - 1) {
      // More steps to go - update tour index
      setTourStepIndex(currentIndex + 1)
    } else {
      // All steps complete
      setIsComplete(true)
      setIsTourActive(false)
      localStorage.setItem(ONBOARDING_STORAGE_KEY, JSON.stringify({
        completedSteps: newCompleted,
        isComplete: true,
      }))
    }
  }

  const skipOnboarding = () => {
    setShowOnboarding(false)
    setIsComplete(true)
    setIsTourActive(false)
    localStorage.setItem(ONBOARDING_STORAGE_KEY, JSON.stringify({
      completedSteps: ONBOARDING_STEPS.map(s => s.id),
      isComplete: true,
    }))
  }

  const nextStep = () => {
    const currentStep = ONBOARDING_STEPS.find(s => !completedSteps.includes(s.id))
    if (currentStep) {
      completeStep(currentStep.id)
    }
  }

  const advanceTour = (targetSelector?: string) => {
    const nextIndex = tourStepIndex + 1
    if (nextIndex < ONBOARDING_STEPS.length) {
      setTourStepIndex(nextIndex)
    } else {
      setIsTourActive(false)
    }
  }

  const currentStep = ONBOARDING_STEPS.find(s => !completedSteps.includes(s.id)) || null
  const tourStep = ONBOARDING_STEPS[tourStepIndex] || null

  return (
    <OnboardingContext.Provider value={{
      currentStep: showOnboarding && !isComplete ? currentStep : null,
      isComplete,
      completedSteps,
      startOnboarding,
      completeStep,
      skipOnboarding,
      nextStep,
      isTourActive,
      tourTarget: isTourActive && tourStep?.targetSelector ? tourStep.targetSelector : null,
      advanceTour,
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