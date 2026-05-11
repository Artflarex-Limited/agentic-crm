# Agentic CRM — Frontend Redesign Design Spec
**Date:** 2026-05-11
**Status:** Draft

---

## 1. Concept & Vision

**"Mission Control for AI Agents"** — Agentic CRM should feel like stepping into a command center where your AI team works. The UI communicates agency, transparency, and intelligent automation. Unlike traditional CRM dashboards that feel like databases with forms, this feels like watching a team at work — live activity feeds, agent status indicators, and an overall sense that the system is alive and working on your behalf.

---

## 2. Design Direction: "AI-Native Command Center"

### Aesthetic Philosophy
- **Dark foundation** with high-contrast data visualization
- **Agent-centric** — agents are visualized as distinct actors, not background processes
- **Live and breathing** — subtle motion everywhere suggests constant activity
- **Data-forward** — numbers and metrics are heroes, not afterthoughts

### Color Palette
| Role | Hex | Usage |
|------|-----|-------|
| Background | `#0a0a0f` | Primary dark background |
| Surface | `#141420` | Cards, panels, sidebar |
| Surface Elevated | `#1c1c2e` | Modals, dropdowns, hover states |
| Border | `#2a2a3e` | Dividers, subtle separators |
| Primary | `#6366f1` | Indigo — primary actions, active states, agent highlights |
| Primary Glow | `#818cf8` | Lighter indigo for hover/glow effects |
| Success | `#10b981` | Emerald — won deals, active agents |
| Warning | `#f59e0b` | Amber — pending approvals, paused agents |
| Danger | `#ef4444` | Red — lost deals, errors, stopped agents |
| Text Primary | `#f1f5f9` | Headings, important data |
| Text Secondary | `#94a3b8` | Body text, labels |
| Text Muted | `#64748b` | Timestamps, helper text |

### Typography
- **Headings:** `Inter` (700, 600) — clean, professional, excellent number rendering
- **Body:** `Inter` (400, 500) — consistent family for cohesion
- **Monospace:** `JetBrains Mono` — for IDs, codes, agent names
- **Scale:** 12/14/16/20/24/32/48px with tight line heights

---

## 3. Layout System

### Sidebar (64px collapsed, 240px expanded)
- Logo + wordmark at top
- Icon-only nav when collapsed, icon + label when expanded
- Bottom: System status indicator (green pulse when agents active)
- Agent presence indicator — avatar dots for active agents

### Main Content Area
- Top bar: Page title + global search + user avatar
- Content: Full-width with 24px padding, max-width 1440px
- Cards use 16px padding, 12px border-radius

### Spatial Rhythm
- **Tight:** 8px — between related elements (badges, tags)
- **Standard:** 16px — between same-level elements (list items)
- **Comfortable:** 24px — between section groupings
- **Loose:** 32-48px — between major sections (pipeline stages)

---

## 4. Key Component Redesigns

### Pipeline Kanban (Dashboard)
- **Horizontal scroll** with 6 stages
- Each stage column: subtle header with count + total value
- Deal cards: dark surface with left border colored by value tier
- **Animated** — new cards slide in, stage transitions animate
- Real-time update indicator (subtle pulse when data refreshes)

### Stats Cards
- Dark card with subtle gradient border (primary color at 20% opacity)
- Large number (32px) with label below
- Sparkline or mini-bar chart showing trend
- Subtle hover: lift + glow

### Agent Status Cards (Agents Page + Sidebar)
- Agent icon + name + role badge
- Status indicator: colored dot (green/amber/red) with label
- **Activity pulse:** active agents show subtle breathing animation on their dot
- Quick action buttons (Pause/Resume/Stop) with icon-only in collapsed view

### Activity Feed
- Timeline-style layout with vertical line
- Each entry: agent avatar, action description, timestamp
- Color-coded by activity type
- Grouped by time (Today, Yesterday, This Week)

### Lead Table
- Alternating row backgrounds (subtle)
- Sortable columns with arrow indicators
- Stage shown as colored badge
- Row hover: entire row highlights subtly

---

## 5. Motion Design

### Principles
- **Purposeful** — motion communicates state change or guides attention
- **Quick** — 150-300ms for micro-interactions
- **Eased** — cubic-bezier(0.4, 0, 0.2, 1) for most transitions

### Specific Animations
| Element | Animation |
|---------|-----------|
| Card hover | translateY(-2px), shadow increase, 200ms |
| Button press | scale(0.98), 100ms |
| Modal open | fade + scale from 0.95, 200ms |
| Status dot (active) | opacity pulse 1 → 0.6 → 1, 2s infinite |
| New item appear | slideIn from right, 300ms |
| Stage change | card slides horizontally to new column, 400ms |
| Loading skeleton | shimmer animation, 1.5s infinite |

---

## 6. Component Specifications

### Button Variants
- **Primary:** Indigo background, white text, glow on hover
- **Secondary:** Surface background, border, text-primary on hover
- **Ghost:** No background, text only, subtle bg on hover
- **Destructive:** Red background, white text

### Badge/Tag System
- Stage badges: colored background matching stage color at 15% opacity + text in full color
- Agent role badges: monospace font, uppercase, small
- Source tags: outline style, muted color

### Card Design
- Background: `#141420`
- Border: 1px `#2a2a3e`
- Border-radius: 12px
- Hover: border-color transitions to primary at 50% opacity

### Data Visualization (Recharts)
- Bar charts: Indigo primary bars, rounded tops
- Colors: Use palette above — success/warning/danger for highlights
- Grid lines: `#2a2a3e` at 50% opacity
- Tooltips: Surface elevated background, subtle border

---

## 7. Open Questions / Next Steps

1. **Color intensity?** — How bold should the primary indigo be? 6366f1 is standard indigo — we could go darker/lighter
2. **Animation budget?** — Are there pages that should be more/less animated?
3. **Mobile approach?** — Responsive design or separate mobile consideration?

---

*This spec will be implemented via frontend-design skill*