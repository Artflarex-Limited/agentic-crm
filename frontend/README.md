# Agentic CRM Frontend

Next.js 14 frontend for the Agentic CRM dashboard.

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** TailwindCSS + shadcn/ui components
- **State:** React Query + Zustand
- **Charts:** Recharts

## Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx         # Root layout with sidebar
│   ├── page.tsx           # Redirects to /dashboard
│   ├── dashboard/         # Dashboard with pipeline Kanban
│   ├── leads/             # Lead management
│   ├── agents/            # Agent status and controls
│   └── settings/          # SMTP, integrations, approvals
├── components/
│   ├── ui/                # shadcn/ui base components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── badge.tsx
│   │   ├── dialog.tsx
│   │   ├── input.tsx
│   │   ├── select.tsx
│   │   ├── table.tsx
│   │   └── label.tsx
│   ├── analytics.tsx      # Dashboard charts and metrics
│   ├── onboarding-modal.tsx
│   └── supplier-waitlist/
├── lib/
│   ├── api.ts             # Typed API client
│   ├── providers.tsx      # React Query provider
│   ├── utils.ts           # Utilities
│   └── tracking.ts        # Analytics helpers
└── public/
```

## Setup

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Environment Variables

Create `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GA4_MEASUREMENT_ID=G-XXXXXXXXXX
NEXT_PUBLIC_HUBSPOT_PORTAL_ID=XXXXXXXX
```

## Pages

| Route | Description |
|-------|-------------|
| `/` | Redirects to `/dashboard` |
| `/dashboard` | Pipeline Kanban, stats, activity feed, agent status |
| `/leads` | Lead table, search/filter, create form, detail drawer |
| `/agents` | Agent monitor, pause/resume, audit log, approval queue |
| `/settings` | SMTP, LinkedIn cookies, Apollo.io, Twilio, outreach toggle |

## API Client

The typed API client in `lib/api.ts` wraps all backend endpoints:

```typescript
import { api } from '@/lib/api'

// Fetch pipeline
const pipeline = await api.dashboard.pipeline()

// List agents
const agents = await api.agents.list()

// Create lead
const newLead = await api.leads.create({ name: '...', email: '...' })
```