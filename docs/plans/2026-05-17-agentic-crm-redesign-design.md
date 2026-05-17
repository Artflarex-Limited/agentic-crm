# Agentic CRM — Full Visual Redesign Design Doc
**Date:** 2026-05-17
**Status:** Approved — Phase 1: Brainstorming complete

---

## 1. Concept & Vision

Agentic CRM feels like a great executive assistant: calm, spacious, warm. Everything is exactly where it should be. Agents work hard in the background; the UI stays serene. Built for sales teams that want AI superpowers without cognitive overload. Think **Linear meets a premium productivity tool** — not a generic SaaS admin panel.

---

## 2. Design Language

### Aesthetic Direction
**"Calm Intelligence"** — Warm, spacious, confident. Every element earns its place. The UI breathes even while agents are executing hundreds of tasks in the background.

### Color Palette
| Role | Value | Notes |
|------|-------|-------|
| Background (base) | `#0A0A0B` | Near-black, warm undertone |
| Background (surface) | `#111113` | Cards and elevated surfaces |
| Background (muted) | `#18181B` | Sidebar, secondary areas |
| Border | `#27272A` | Subtle borders |
| Border (hover) | `#3F3F46` | Interactive border states |
| Text (primary) | `#FAFAFA` | Headings, key content |
| Text (secondary) | `#A1A1AA` | Body text, labels |
| Text (muted) | `#71717A` | Placeholders, tertiary |
| **Accent (primary)** | `#F59E0B` | **Amber-500** — signature brand color |
| Accent (hover) | `#D97706` | Amber-600 for hover states |
| Accent (subtle) | `#F59E0B/10` | Amber at 10% for tints |
| Accent (muted) | `#F59E0B/20` | Amber at 20% for backgrounds |
| Success | `#10B981` | Emerald-500 |
| Warning | `#F59E0B` | Amber (same as accent — intentional) |
| Danger | `#EF4444` | Red-500 |
| Info | `#60A5FA` | Blue-400 |

### Typography
- **Display / Headings:** Hanken Grotesk (600, 700 weights) — warm geometric sans with personality
- **Body / UI:** Inter (400, 500 weights) — high legibility at small sizes
- **Monospace:** JetBrains Mono — agent logs, IDs, timestamps
- **Scale:** 12 / 14 / 16 / 18 / 20 / 24 / 30 / 36 / 48px with tight tracking on headings (-0.02em)
- **Line heights:** 1.2 for headings, 1.5 for body, 1.6 for large text

### Spatial System
- Base unit: 4px
- Common spacings: 8, 12, 16, 20, 24, 32, 40, 48, 64px
- Card padding: 24px
- Section gaps: 24–32px
- Generous whitespace between sections — let content breathe

### Motion Philosophy
- **Entrance:** fade-in + subtle translateY(8px), 200ms ease-out, staggered 50ms between cards
- **Hover:** scale(1.01) on cards, 150ms ease — subtle, never distracting
- **State changes:** 150ms ease for color/opacity transitions
- **Page transitions:** 200ms fade between routes
- **No aggressive animations** — "calm" means no bounce, no spring, no looping effects unless conveying live state (pulsing dots for active agents)
- Live data indicators: gentle pulse (opacity 0.5→1→0.5), 2s cycle

### Visual Assets
- **Icons:** Lucide React — consistent 1.5px stroke weight, 24px default size, 16px in compact contexts
- **Decorative:** Subtle amber glow effects on key CTAs (box-shadow with amber/20). Thin amber gradient top-border on feature cards.
- **Agent avatars:** Rounded squares (radix-style), amber-tinted for active state
- **Empty states:** Custom inline SVG illustrations with muted amber linework
- **Charts:** Recharts with the amber/emerald/slate palette — no default blue

### Border Radius
- Cards: 12px
- Buttons: 8px
- Badges: 6px
- Inputs: 8px
- Avatars: 8px (rounded square)

---

## 3. Layout & Structure

### Page Architecture
- **Sidebar (64px collapsed / 240px expanded):** Fixed left. Dark muted background. Logo + nav icon rail + expand trigger + user avatar at bottom.
- **Top bar (56px):** Page title (left) + breadcrumb context + global search (⌘K) + notification bell + user menu (right). Sticky.
- **Content area:** Single-column card stack, max-width 1200px centered, 32px horizontal padding, 24px vertical gaps between cards.
- **Responsive:** Sidebar collapses to icon rail at <1024px, hides to hamburger drawer at <768px.

### Visual Pacing
- Hero/header section of each page: generous 48px top padding, page title large and prominent
- Card sections: tight 24px internal padding, 24px gap between cards
- Footer elements (last updated, quick links): 40px below last content card

---

## 4. Page-by-Page Redesign

### 4.1 Landing Page
**Goal:** Convert visitors. Convey "AI agent power without the chaos."

**Hero Section:**
- Large display heading (48px), amber accent on key phrase
- Subheading in secondary text, max 2 lines
- Two CTAs: "Try the Demo" (amber filled) + "Watch Video" (ghost button)
- Background: subtle radial gradient from `#F59E0B/5` at center, fading to base
- Right side (or below on mobile): minimal animated mockup — a tiny live pipeline card with amber dots pulsing for "active agents"

**Social Proof Strip:**
- "Trusted by X sales teams" + 4–6 placeholder company logos (greyscale SVG)
- 3 key stats: "50K+ leads sourced", "12ms avg response", "Open source"

**Features Section:**
- 4 feature cards in a 2×2 grid (not 2-column list)
- Each card: icon (amber tint background) + heading + body + subtle amber top-border gradient
- Clean, editorial feel — generous padding in each card

**Demo Section:**
- Replace Loom placeholder with a rich static mockup (styled app screenshot) + play button overlay
- Fallback if real video is unavailable

**Benefits List:**
- 2-column grid of benefit rows (checkmark + text), not a bulleted list

**Pricing Section (new — currently missing):**
- 3 tiers: Free / Pro / Enterprise
- Pro tier highlighted with amber border glow
- Annual/monthly toggle at top

**Footer:**
- Minimal: logo + tagline + links + copyright
- Links: GitHub, Docs, Privacy, Terms

### 4.2 Dashboard
**Goal:** Mission control at a glance — structured, calm, scannable.

**Layout:** Single-column card stack (per spatial system)

**Hero Metrics Strip (4 cards in a row, equal width):**
- Total Leads, Open Deals Value, Won This Month, Active Agents
- Each: icon (amber bg) + large number + label + subtle trend indicator
- Trend: small arrow icon + percentage + "vs last month" in muted text

**Pipeline Overview Card (full width):**
- Full-width bar chart showing deal counts per stage
- Amber bars, rounded, with stage labels below
- Clicking a stage filters the leads table below

**Two-Column Lower Section:**
- Left: Conversion Funnel (vertical bars or dot-matrix) + Revenue Forecast table
- Right: Recent Agent Activity feed (timeline, newest at top) + Source Effectiveness list

**Quick Actions Bar (new):**
- Right below metrics: "Create Lead", "Trigger Agent", "Send Outreach" — amber outlined buttons in a row

**Live Indicator:**
- Subtle "● Live" badge in top-right of page header (not just a pulsing dot — actual label)

### 4.3 Leads Page
**Goal:** Find, filter, and act on leads without friction.

**Layout:** Filters bar → View toggle (Table/Kanban) → Leads display

**Filters Bar:**
- Horizontal: search input (with amber focus ring) + Stage dropdown + Source dropdown + Clear button
- Debounced 300ms search (already implemented, keep)

**View Toggle (new):**
- Pill toggle: "Table" / "Kanban" — inline in the filters bar
- Table view: existing implementation, styled with new typography and border treatment
- Kanban view: drag-and-drop columns per stage, lead cards showing avatar + name + company + score badge

**Lead Table (redesigned):**
- Lighter row hover state (subtle bg shift)
- Score shown as a mini progress bar with amber fill (keep existing logic)
- Last Contacted as relative time ("3 days ago") instead of full date
- Row click → opens slide-over drawer (not dialog modal)

**Lead Detail Drawer (new):**
- Slides in from right, 480px wide
- Header: avatar + name + stage badge + quick action buttons (Email, LinkedIn, Edit)
- Tabs: Overview / Activity / Notes
- Overview: contact fields, company, source, score, created date
- Activity: timeline of all agent actions + manual entries
- Notes: plain text area with save

**Bulk Actions (new):**
- Checkbox column on left of table
- When 1+ selected: floating action bar slides up from bottom with: Change Stage, Change Owner, Delete

**Add Lead Modal:**
- Keep existing dialog but restyle: amber focus rings, cleaner field spacing, better validation UX

### 4.4 Agents Page
**Goal:** See your AI team, understand what they're doing, stay in control.

**Layout:** Header + Agent Cards Grid (2 columns) + Sidebar (Approval Queue + Activity Feed)

**Agent Cards:**
- Larger, more spacious cards in 2-column grid
- Header: agent icon (large, amber-tinted) + name + role badge + status pill
- Body: description text (truncated) + created date
- Footer: action buttons (Resume/Pause/Stop) + Activity Log expand toggle
- Expanded state: scrollable activity log inline, not a new page

**Agent Config Button (new):**
- Each card gets a subtle settings gear icon in top-right corner
- Opens a slide-over panel to configure: target criteria, outreach limits, schedule

**Approval Queue (promoted):**
- Currently a sidebar card — elevate to a sticky right panel (240px) on the agents page
- Each item: message + agent name badge + timestamp + Approve/Deny buttons
- Empty state: checkmark + "All clear" message in emerald

**Activity Feed (right panel):**
- Compact timeline, newest at top
- Each item: agent avatar dot + message + timestamp
- "Load more" at bottom

**Agent Creation (new):**
- "Create Agent" button in header → opens modal with: name, role (dropdown), description, configuration

### 4.5 Settings Page
**Goal:** Configure the CRM without it feeling like a developer panel.

**Layout:** Left tab rail (vertical tabs) + right content area

**Tabs:**
- Profile (name, email, avatar upload)
- Notifications (email/Slack/in-app toggles)
- Integrations (LinkedIn, Email, HubSpot — connection status + disconnect button)
- Team (invite members, role assignment — shown as table with avatar + email + role + remove)
- API Keys (list + create + revoke)
- Danger Zone (export data, delete account — red bordered section)

**Styling:** Each tab section is a card with 24px padding. Form fields use amber focus rings. Toggle switches styled with amber active state.

### 4.6 Onboarding (New — if missing)
**Goal:** Get a new user to their first lead in under 5 minutes.

**Onboarding Modal (refactor):**
- Currently exists — restyle to match new design language
- Step 1: Connect email/LinkedIn
- Step 2: Import first lead source
- Step 3: Meet your first agent
- Progress stepper with amber fill

---

## 5. Component Inventory

### Buttons
- **Primary:** Amber bg, dark text, 8px radius, hover darkens to Amber-600
- **Secondary:** Transparent + border, text secondary, hover fills bg-secondary
- **Ghost:** Text only, hover shows subtle bg
- **Danger:** Red-500 bg, white text
- **Loading state:** Spinner icon replaces text, disabled

### Cards
- 12px radius, `#111113` background, `#27272A` border, 24px padding
- Hover: border lightens to `#3F3F46`, subtle translateY(-2px), 150ms ease
- Active/selected: amber border glow

### Badges
- 6px radius, small (12px text), amber-tinted for stages, slate-tinted for sources
- Status badges with colored dot prefix

### Inputs
- 8px radius, `#111113` background, `#27272A` border
- Focus: amber ring (2px, `#F59E0B/40`)
- Error: red border + red helper text below

### Dialog / Drawer
- Dialog: centered, max-w-500, 12px radius, backdrop blur
- Drawer: right-side slide-in, 480px, same border treatment as cards

### Sidebar Nav
- Icon + label, 40px row height, 8px radius
- Active: amber-tinted bg (`#F59E0B/10`) + amber text + left amber border indicator
- Hover: bg-secondary transition

### Tables
- Light border between rows (`#27272A/50`)
- Header: uppercase 12px, letter-spacing 0.05em, text-muted
- Row hover: bg-secondary/50

### Charts
- Bar chart: Amber-500 bars, rounded tops
- Line chart: Amber-500 stroke, no fill, subtle grid lines
- Donut chart: Amber/Emerald/Slate palette

---

## 6. Technical Approach

### Stack
- **Framework:** Next.js 14 (App Router) — existing, keep
- **Styling:** Tailwind CSS + CSS custom properties for design tokens
- **Components:** Radix UI (existing) + custom-styled wrappers
- **Animation:** Tailwind + CSS transitions (no Framer Motion needed for "calm" motion)
- **State:** Zustand (existing) + TanStack Query (existing)
- **Charts:** Recharts (existing)

### Design Token Implementation
All colors via CSS custom properties in `globals.css`:
```css
:root {
  --color-bg-base: #0A0A0B;
  --color-bg-surface: #111113;
  --color-bg-muted: #18181B;
  --color-border: #27272A;
  --color-border-hover: #3F3F46;
  --color-text-primary: #FAFAFA;
  --color-text-secondary: #A1A1AA;
  --color-text-muted: #71717A;
  --color-accent: #F59E0B;
  --color-accent-hover: #D97706;
  --color-accent-subtle: rgba(245, 158, 11, 0.1);
  --color-accent-muted: rgba(245, 158, 11, 0.2);
  --color-success: #10B981;
  --color-danger: #EF4444;
}
```
Tailwind config maps these to utility classes.

### Font Loading
```jsx
// app/layout.tsx
<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
```
`font-family: 'Hanken Grotesk'` for headings, `'Inter'` for body, `'JetBrains Mono'` for mono.

### Key Implementation Notes
- All animations via CSS transitions, no external animation library needed
- Kanban drag-and-drop: `@dnd-kit/core` (lightweight, works with React)
- Slide-over drawer: custom Radix Dialog with `side="right"` + CSS transform animation
- Charts: Recharts with custom amber theme tokens
- Skeleton loaders: custom CSS `@keyframes pulse` with `bg-secondary` animation

---

## 7. Out of Scope (YAGNI)

- Push notifications / real-time WebSocket updates (polling is fine for MVP)
- Email sequencing editor (keep as backend feature, not redesigned yet)
- Custom agent builder / workflow canvas (Phase 2)
- White-labeling / theming (Phase 2)
- Mobile responsive beyond basic layout collapse (Phase 2)

---

## 8. Success Criteria

- [ ] Every page feels cohesive — same font, same palette, same spacing rhythm
- [ ] "Calm intelligence" is real: no page feels cluttered or overwhelming
- [ ] Sidebar is collapsible, responsive, and visually refined
- [ ] Landing page converts: clear hero, social proof, pricing
- [ ] Dashboard is scannable in <10 seconds
- [ ] Lead detail is a drawer, not a modal
- [ ] Kanban view for leads is functional
- [ ] Approval queue is prominent and actionnable
- [ ] All interactive elements have hover/focus/active states
- [ ] Empty states have meaningful messaging
- [ ] No placeholder content (Loom embed, fake stats)