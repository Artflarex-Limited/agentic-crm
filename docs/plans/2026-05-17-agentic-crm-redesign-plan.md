# Agentic CRM — Full Visual Redesign Implementation Plan
**Date:** 2026-05-17
**Design Doc:** `docs/plans/2026-05-17-agentic-crm-redesign-design.md`

---

## Execution Mode

**Subagent-driven per task** — one task at a time, each executed and reviewed before moving to the next.

---

## Task List

### Foundation (must complete first, in order)

- [ ] **T1 — Design Tokens & CSS Variables**
  Add all CSS custom properties to `globals.css`, remove/adjust Tailwind config to use the new palette.
  File: `frontend/app/globals.css`
  Verify: `globals.css` contains all `--color-*` variables from design doc

- [ ] **T2 — Tailwind Config Update**
  Map CSS variables to Tailwind utilities, add amber as primary, update border/text color extensions.
  File: `frontend/tailwind.config.ts`
  Verify: `amber-500` utilities resolve to `#F59E0B`, backgrounds to correct hex values

- [ ] **T3 — Font Loading**
  Load Hanken Grotesk + Inter + JetBrains Mono in `app/layout.tsx`.
  File: `frontend/app/layout.tsx`
  Verify: Page uses correct font families — check computed styles in browser/DevTools

- [ ] **T4 — Global Styles & Base**
  Add `@layer base` global styles, font-feature-settings, selection color, scrollbar styling, focus rings using amber.
  Files: `frontend/app/globals.css`
  Verify: No default blue focus rings; amber ring on inputs; custom scrollbar

- [ ] **T5 — Component Library Restyle**
  Restyle: Card, Button, Badge, Input, Select, Dialog, Table — using new tokens and border-radius system.
  Files: `frontend/components/ui/*.tsx`
  Verify: All components use new tokens; hover/focus states work; radius is 12/8/6/8px

---

### Landing Page

- [ ] **T6 — Landing: Layout & Typography**
  Update hero text sizes, spacing, remove generic gradient. Add radial amber glow background.
  Files: `frontend/app/page.tsx`, `frontend/app/globals.css`
  Verify: Hero has amber accent, proper typography scale, radial glow bg

- [ ] **T7 — Landing: Features 2×2 Grid**
  Replace 2-column list with 2×2 card grid, add amber top-border accent per card.
  File: `frontend/app/page.tsx`
  Verify: 2×2 grid, amber border-top on each card, proper padding

- [ ] **T8 — Landing: Social Proof + Stats Strip**
  Add above features section — greyscale logos + 3 stat counters.
  File: `frontend/app/page.tsx`
  Verify: Logos visible, stats displayed

- [ ] **T9 — Landing: Pricing Section**
  Build 3-tier pricing section (Free/Pro/Enterprise) with amber-highlighted Pro tier.
  File: `frontend/app/page.tsx`
  Verify: 3 tiers, Pro tier has amber border glow, toggle visible

- [ ] **T10 — Landing: Demo Replace**
  Replace Loom PLACEHOLDER with styled fallback mockup + play button. Add amber ring focus.
  File: `frontend/app/page.tsx`
  Verify: No broken iframe, has styled placeholder with play button

- [ ] **T11 — Landing: Footer**
  Restyle footer with minimal links, logo, amber accent.
  File: `frontend/app/page.tsx`
  Verify: Clean footer, correct links

---

### Layout & Navigation

- [ ] **T12 — Sidebar Restyle**
  Update sidebar to dark muted (`#18181B`), amber active states, collapsible with smooth animation.
  Files: `frontend/app/layout.tsx`
  Verify: Sidebar uses `#18181B` bg, amber active indicator, collapse animation works

- [ ] **T13 — Top Bar Restyle**
  Restyle header: search input amber focus ring, user avatar, live badge.
  File: `frontend/app/layout.tsx`
  Verify: Search amber ring on focus, live badge visible

---

### Dashboard

- [ ] **T14 — Dashboard: Metrics Strip**
  Update 4 hero metric cards: amber icon backgrounds, proper typography, trend indicators.
  Files: `frontend/app/dashboard/page.tsx`
  Verify: Cards use new tokens, amber icon bg, trend arrows visible

- [ ] **T15 — Dashboard: Pipeline Chart**
  Style pipeline bar chart with amber bars, rounded tops.
  Files: `frontend/components/analytics.tsx` (or inline in dashboard)
  Verify: Amber bars, stage labels, click filtering works

- [ ] **T16 — Dashboard: Lower Grid**
  Rebuild lower section: left column = Conversion Funnel + Revenue Forecast; right column = Agent Activity + Source Effectiveness.
  File: `frontend/app/dashboard/page.tsx`
  Verify: Single-column stack above, two-column grid below, cards use new token

- [ ] **T17 — Dashboard: Quick Actions Bar**
  Add "Create Lead", "Trigger Agent", "Send Outreach" amber outline buttons below metrics.
  File: `frontend/app/dashboard/page.tsx`
  Verify: 3 action buttons visible, amber outline style

---

### Leads Page

- [ ] **T18 — Leads: View Toggle**
  Add Table/Kanban pill toggle in filters bar.
  Files: `frontend/app/leads/page.tsx`
  Verify: Toggle visible, switches between views

- [ ] **T19 — Leads: Table Restyle**
  Restyle table: lighter row hover, amber score progress bar, relative time for Last Contacted.
  File: `frontend/app/leads/page.tsx`
  Verify: Row hover subtle, amber score bar, relative timestamps

- [ ] **T20 — Leads: Kanban View**
  Build Kanban view: draggable columns by stage, lead cards with avatar + name + score.
  File: `frontend/app/leads/page.tsx`
  Verify: All stages have columns, cards draggable between stages

- [ ] **T21 — Leads: Drawer (replace modal)**
  Convert lead detail modal → right-side slide-over drawer (480px).
  File: `frontend/app/leads/page.tsx`
  Verify: Drawer slides from right, tabs work, no scroll on main page

- [ ] **T22 — Leads: Bulk Actions**
  Add checkbox column + floating bottom action bar for multi-select stage changes.
  File: `frontend/app/leads/page.tsx`
  Verify: Checkboxes appear, floating bar shows on selection

---

### Agents Page

- [ ] **T23 — Agents: Card Grid Restyle**
  Restyle agent cards: larger spacing, amber icon backgrounds, hover lift.
  Files: `frontend/app/agents/page.tsx`
  Verify: 2-column grid, amber icon tint, hover scale effect

- [ ] **T24 — Agents: Agent Config Panel**
  Add settings gear → slide-over config panel for target criteria, outreach limits.
  File: `frontend/app/agents/page.tsx`
  Verify: Gear icon visible per card, config drawer opens

- [ ] **T25 — Agents: Approval Queue Panel**
  Promote approval queue from sidebar card → sticky right panel (240px).
  File: `frontend/app/agents/page.tsx`
  Verify: Approval queue in right panel, approve/deny buttons work

- [ ] **T26 — Agents: Activity Feed Restyle**
  Compact timeline in right panel, amber dot indicators.
  File: `frontend/app/agents/page.tsx`
  Verify: Compact feed visible, load more works

- [ ] **T27 — Agents: Create Agent Modal**
  Build agent creation modal with name/role/description/config fields.
  File: `frontend/app/agents/page.tsx`
  Verify: Modal opens, fields styled with amber focus rings, creates on submit

---

### Settings Page

- [ ] **T28 — Settings: Tab Rail + Content Cards**
  Add left tab rail (Profile/Notifications/Integrations/Team/API/Danger Zone) + restyle each section as a card.
  Files: `frontend/app/settings/page.tsx`
  Verify: Tabs switch content, all 6 sections exist, amber active tab indicator

- [ ] **T29 — Settings: Form Styling**
  Apply amber focus rings to all form fields, styled toggles, danger zone red border.
  File: `frontend/app/settings/page.tsx`
  Verify: All inputs have amber focus, toggles amber when active, danger zone red-bordered

---

### Polish

- [ ] **T30 — Skeleton Loaders**
  Replace any remaining `className="skeleton"` with proper CSS keyframe skeleton components.
  Files: `frontend/app/dashboard/page.tsx`, `frontend/app/leads/page.tsx`, `frontend/app/agents/page.tsx`
  Verify: Skeleton has pulsing animation, correct shapes per context

- [ ] **T31 — Empty States**
  Add meaningful empty state messages + subtle amber SVG illustrations across all pages.
  Files: All page files + `frontend/components/ui/empty-state.tsx`
  Verify: Empty states show meaningful copy + icon, no blank spaces

- [ ] **T32 — Global Animations**
  Add entrance animations (fade-in + translateY), hover transitions per design doc.
  Files: `frontend/app/globals.css`
  Verify: Page elements fade in on load, cards lift on hover

- [ ] **T33 — Final Smoke Test**
  Run through every page, verify no broken layouts, console errors, or mismatched colors.
  Command: `cd /root/agentic-crm/frontend && npm run build`
  Verify: Build succeeds with zero errors

---

## Verification Command (per task)

After each task:
```bash
cd /root/agentic-crm/frontend && npm run build
```
Build must succeed with no TypeScript errors or missing imports.

---

## Notes

- Tasks T1–T5 (Foundation) must be completed before any page restyling — all pages depend on the token system.
- Tasks are ordered to minimize dependency conflicts. Complete T1–T5 before T6+.
- Kanban drag-and-drop requires `@dnd-kit/core` — install before T20 if not already present.
- If any page references a color not in the design token list, add it to both `globals.css` and `tailwind.config.ts` before using.
- The `analytics.tsx` component contains chart components used by dashboard — review and restyle in-place during T14–T16.