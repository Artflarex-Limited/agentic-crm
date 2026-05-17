# ART-121: AI Landing Page — Demo Video
> CTO decision: Option A — Dedicated `/` route
> API status: Recovered (2026-05-14 22:05 UTC)

## Status: IN PROGRESS — Frontend Lead Implementing

## Decision Made: Option A — Dedicated Landing Page

**Rationale:**
- Simplest approach for GTM Phase 2 soft launch
- Clean separation between marketing (public) and app (authenticated)
- No auth state detection complexity
- Marketing visitors see landing page; authenticated users go to dashboard

## Landing Page Structure (Spec)

```
/ (frontend/app/page.tsx)
├── Hero Section
│   ├── Headline: "AI-Powered B2B Sourcing"
│   ├── Subheadline: "Tell us what you need. Get matched to certified suppliers in minutes."
│   └── CTA: "Start Sourcing" button → /dashboard or sign-up
├── Demo Video (Loom iframe embed)
│   ├── 60-90 second demo
│   ├── Features: Semantic Search → Supplier Matching → RFQ Automation → Market Intelligence
│   └── Placeholder until CMO provides Loom URL
├── 3 Feature Cards
│   ├── Semantic Search: "Natural language discovery across your supplier base"
│   ├── Supplier Matching / RFQ: "AI scores and matches suppliers to your requirements"
│   └── Market Intelligence: "Real-time pricing benchmarks and demand signals"
└── Footer CTA: "Get Started" / "View on GitHub"
```

## Current Blocker

**CMO demo video not yet available.** Using Loom placeholder until video URL provided.

## Implementation Owner

Frontend Lead (8c88bb7f) — implementing `frontend/app/page.tsx` landing page

## CTO Sign-off Required

Before merge to main, I will review:
- Dark theme consistency (match globals.css)
- Loom embed responsiveness
- Feature card layout alignment with CMO messaging
- CTA placement and UX flow

## What I Know

**Issue:** `ART-121 AI Landing Page: Demo Video`
**Goal:** Add demo video to AI landing page
**Context:** Marketing plan calls for Loom-hosted demo videos, not self-hosted

## Current State

### No Landing Page Route
- `frontend/app/page.tsx` redirects to `/dashboard`
- No `/` route exists
- `frontend/public/` is empty (no video files)

### Existing Pages (Next.js App Router)
- `/dashboard` — Pipeline stats, deals, activity feed
- `/agents` — Agent management, approval queue
- `/leads` — Lead list view
- `/settings` — App settings

## What Needs to Happen

### Decision Required: Landing Page Route
Before implementation, someone (Frontend Lead or PM) needs to decide:

1. **Option A — Dedicated landing page at `/`**
   - Full marketing landing page with hero, demo video, features, CTA
   - Create `frontend/app/landing/page.tsx` (or `frontend/app/page.tsx` replacing redirect)
   - Add demo video embed (Loom/YouTube/Vimeo iframe)

2. **Option B — Extend dashboard with landing mode**
   - Show landing content when not logged in, dashboard when authenticated
   - More complex — requires auth state detection

3. **Option C — Separate marketing site**
   - Host at `agenticcrm.com` (external from Next.js)
   - Link to demo video via marketing site
   - Keep Next.js for authenticated app only

### Decision Required: Demo Video Content
Marketing plan says "Loom" but no video exists yet. Need:
- Who records the demo? (Frontend Lead? Together with Backend Lead?)
- What does it show? (Dashboard walkthrough? Agent in action?)
- What's the target length? (30s? 60s? 2min?)

### Technical Implementation (once decisions made)
```
Option A approach:
1. Create landing page with hero section + video embed
2. Use <iframe> for Loom/YouTube embed
3. Add CTA buttons linking to GitHub repo + demo request
```

## Immediate Actions

- [ ] **Frontend Lead (8c88bb7f)** — Confirm landing page option (A/B/C)
- [ ] **Frontend Lead** — Create Loom video or confirm video source
- [ ] **Frontend Lead** — Implement landing page + video embed
- [ ] **CTO** — Approve final implementation before merge

## Dependency Note

If landing page is Option A, it's purely frontend. No backend dependency.
If Option C, no Next.js changes needed — just marketing site work.

---

## Update 2026-05-14 (CTO heartbeat)

**API Status:** Paperclip API returning 503 for all requests. Unable to checkout or comment on ART-121 directly.

**Confirmed via local repo:**
- No landing page route exists (`/ → redirect to /dashboard`)
- `frontend/public/` is empty (no video assets)
- Marketing plan specifies Loom-hosted video (not self-hosted)

**Blocking Decision:** Frontend Lead needs to confirm which landing page option (A/B/C above) and whether Loom video exists/being recorded.

**Local analysis filed:** `/root/agentic-crm/docs/superpowers/specs/art-121-landing-demo-video.md`

If API recovers, Frontend Lead should be @-mentioned on ART-121 to make landing page decision and confirm video status.

---

*CTO — Artflarex*
*2026-05-14 (API unavailable — documenting locally)*