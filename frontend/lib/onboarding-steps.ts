export type OnboardingStep = {
  id: string
  title: string
  description: string
  action: string
  targetSelector?: string
  page?: string
}

export const ONBOARDING_STEPS: OnboardingStep[] = [
  {
    id: 'welcome',
    title: 'Welcome to Agentic CRM',
    description: 'Your AI-powered sales team is ready to help you convert leads and close deals.',
    action: 'Get Started',
  },
  {
    id: 'dashboard',
    title: 'Dashboard Overview',
    description: 'Monitor your pipeline, track agent activity, and view key metrics at a glance.',
    action: 'Explore Dashboard',
    targetSelector: '[data-tour="dashboard"]',
    page: '/dashboard',
  },
  {
    id: 'add-lead',
    title: 'Add Your First Lead',
    description: 'Start by adding a lead manually or let your AI agents find prospects for you.',
    action: 'Add Lead',
    targetSelector: '[data-tour="add-lead"]',
    page: '/leads',
  },
  {
    id: 'agents',
    title: 'Meet Your AI Agents',
    description: 'Your agents are working 24/7 to find, qualify, and nurture leads.',
    action: 'View Agents',
    targetSelector: '[data-tour="agents"]',
    page: '/agents',
  },
  {
    id: 'settings',
    title: 'Configure Integrations',
    description: 'Connect your email, LinkedIn, and phone systems to enable full automation.',
    action: 'Configure Settings',
    targetSelector: '[data-tour="settings"]',
    page: '/settings',
  },
]

export const ONBOARDING_STORAGE_KEY = 'agentic-crm-onboarding-completed'