# ART-131 — Supplier Waitlist Landing Page Design Spec

## 1. Concept & Vision

A pre-launch waitlist capture page for Turkish and EU suppliers interested in joining the Agentic CRM supply network. The page conveys trust, professionalism, and the value of early access to an AI-powered supplier discovery platform. It feels like an invitation to be part of something exclusive — not a generic "sign up for updates" form.

---

## 2. Design Language

### Aesthetic Direction
Enterprise-professional with subtle warmth. Think: a premium B2B marketplace meets fintech onboarding. Clean, spacious, and authoritative — with a hint of approachability through copy tone.

### Color Palette
- **Primary:** `#6366F1` (Indigo-500 — trustworthy, modern)
- **Primary Dark:** `#4F46E5` (Indigo-600 — hover states)
- **Secondary:** `#0F172A` (Slate-900 — headlines, strong text)
- **Accent:** `#10B981` (Emerald-500 — success states, CTAs)
- **Background:** `#FFFFFF` (White — main)
- **Background Alt:** `#F8FAFC` (Slate-50 — sections)
- **Border:** `#E2E8F0` (Slate-200)
- **Text Primary:** `#0F172A` (Slate-900)
- **Text Muted:** `#64748B` (Slate-500)

### Typography
- **Headlines:** Inter (700 weight), fallback: system-ui
- **Body:** Inter (400/500 weight)
- **Scale:** Hero: 48px, H2: 32px, H3: 20px, Body: 16px

### Spatial System
- Max content width: 1200px
- Section padding: 96px vertical (desktop), 64px (mobile)
- Component spacing: 24px between cards/elements
- Form field spacing: 16px

### Motion Philosophy
- Subtle fade-in on scroll (opacity 0→1, translateY 20px→0, 400ms ease-out)
- Form button: scale(1.02) on hover, 150ms
- Success state: smooth height expansion with checkmark animation

### Visual Assets
- Icons: Lucide React (already used in the codebase)
- No stock photos — use abstract geometric patterns or gradient overlays
- Decorative: subtle dot grid pattern in hero background

---

## 3. Layout & Structure

### Page Sections (top to bottom)

1. **Navigation Bar** (sticky)
   - Logo + "Agentic CRM" wordmark (left)
   - Single CTA button: "Join Waitlist" (right, scrolls to form)

2. **Hero Section**
   - Headline: "Connecting Turkish & EU Suppliers to AI-Powered Procurement"
   - Subheadline: "Be first to access our network of verified manufacturers. Join the waitlist for early access."
   - Trust badges row: "500+ Suppliers", "24/7 AI Matching", "EU GDPR Compliant"
   - Primary CTA: "Join the Waitlist" (scrolls to form)
   - Visual: Abstract gradient mesh or geometric pattern (no stock photos)

3. **Value Proposition Section** (3 columns)
   - Column 1: Verified Suppliers (icon: ShieldCheck)
   - Column 2: AI Matching (icon: Brain)
   - Column 3: Fast Onboarding (icon: Zap)
   Each card: icon, title, 2-sentence description

4. **How It Works** (3 steps, horizontal timeline)
   - Step 1: Submit Details — "Fill out the supplier form in under 5 minutes"
   - Step 2: Get Verified — "Our team reviews and verifies your business"
   - Step 3: Access Network — "Start receiving AI-matched RFQs from buyers"

5. **Supplier Benefits** (alternating image/text, 2 rows)
   - Row 1: "Reach EU Buyers" — text left, abstract graphic right
   - Row 2: "AI-Powered Matching" — graphic left, text right

6. **Waitlist Form Section** (centered, elevated card)
   - Form card with shadow, containing all fields
   - Success state replaces form after submission

7. **Social Proof / Testimonials** (optional, 2–3 cards)
   - Format: Quote, company name, role

8. **Footer**
   - Logo + tagline
   - Links: Privacy Policy, Terms, Contact
   - Copyright: "© 2026 Artflarex Solutions"

### Responsive Strategy
- Desktop: Full 3-column grids, horizontal timelines
- Tablet (768px): 2-column grids, stacked where needed
- Mobile (480px): Single column, full-width form

---

## 4. Form Fields

### Supplier Waitlist Form

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| Company Name | text | Yes | min 2 chars |
| Country | select | Yes | Must be Turkey or EU country |
| Business Email | email | Yes | Valid email format |
| Phone Number | tel | No | International format |
| Company Website | url | No | Must start with http:// or https:// |
| Industry/Category | select | Yes | Dropdown of categories |
| Annual Production Capacity | select | Yes | Range options |
| Certifications (e.g., CE, ISO) | multi-select | No | Checkbox list |
| Currently Exporting to EU | toggle | No | Yes/No |
| Brief Company Description | textarea | No | max 500 chars |

### Industry Categories (dropdown)
- Electronics & Components
- Automotive Parts
- Textile & Garments
- Food & Beverages
- Machinery & Equipment
- Chemicals & Materials
- Furniture & Fixtures
- Other (specify)

### Success State
After form submission:
- Form replaced with success message
- "Thank you, [Company Name]! You're #X on the waitlist."
- "We'll notify you at [email] when it's your turn."
- Share buttons (optional): LinkedIn, Twitter

---

## 5. Component Inventory

### Navigation Bar
- **Default:** White background, subtle bottom border, logo left, CTA right
- **Scrolled:** Adds shadow
- **Mobile:** Same layout (CTA becomes smaller)

### Hero CTA Button
- **Default:** Primary color, white text, rounded-lg, px-6 py-3
- **Hover:** Primary-dark, slight scale up
- **Active:** Pressed state (scale 0.98)
- **Loading:** Spinner replaces text

### Value Proposition Card
- **Default:** White bg, border, rounded-xl, icon top, text below
- **Hover:** Border color shifts to primary/30, subtle shadow lift

### Form Input Field
- **Default:** Border-slate-200, rounded-md, h-10
- **Focus:** Ring-2 primary/50, border-primary
- **Error:** Border-red-500, error message below
- **Disabled:** Opacity 50, cursor not-allowed

### Form Submit Button
- **Default:** Primary bg, white text, full width
- **Hover:** Primary-dark
- **Loading:** Spinner + "Submitting..."
- **Disabled:** Opacity 50

### Success Card
- **State:** Replaces form, emerald checkmark icon, confirmation text

---

## 6. Technical Approach

### Framework
- Next.js 14 App Router (same as existing frontend)
- TypeScript
- TailwindCSS (already configured)
- Lucide React icons (already installed)
- React Hook Form + Zod for form handling

### File Structure
```
frontend/
  app/
    supplier-waitlist/
      page.tsx          # Main landing page
      page.module.css   # Any page-specific styles
  components/
    supplier-waitlist/
      HeroSection.tsx
      ValueProps.tsx
      HowItWorks.tsx
      BenefitsSection.tsx
      WaitlistForm.tsx
      SuccessState.tsx
```

### Form Submission
- Client-side validation with Zod schema
- POST to `/api/waitlist/supplier` (new endpoint)
- Success state managed with React state
- Error handling: show inline error messages

### API Endpoint (new)
```
POST /api/waitlist/supplier
Body: {
  company_name: string,
  country: string,
  business_email: string,
  phone?: string,
  website?: string,
  industry: string,
  production_capacity: string,
  certifications: string[],
  exporting_to_eu: boolean,
  description?: string
}
Response: { success: true, position: number }
```

### Success Metrics (per spec)
- Form submission rate
- Waitlist position display
- Email confirmation sent

---

## 7. Self-Review Checklist

- [ ] No placeholder text or TODOs
- [ ] All form fields have validation rules
- [ ] Mobile responsive at all breakpoints
- [ ] Loading and success states handled
- [ ] Design matches existing Agentic CRM aesthetic
- [ ] No external dependencies beyond what we have
- [ ] API contract is clear and testable