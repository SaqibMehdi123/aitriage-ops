---
name: AITriage Ops
colors:
  surface: '#f9f9ff'
  surface-dim: '#d3daea'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f0f3ff'
  surface-container: '#e7eefe'
  surface-container-high: '#e2e8f8'
  surface-container-highest: '#dce2f3'
  on-surface: '#151c27'
  on-surface-variant: '#474553'
  inverse-surface: '#2a313d'
  inverse-on-surface: '#ebf1ff'
  outline: '#787584'
  outline-variant: '#c8c4d5'
  surface-tint: '#584fbc'
  primary: '#3b309e'
  on-primary: '#ffffff'
  primary-container: '#534ab7'
  on-primary-container: '#d1ccff'
  inverse-primary: '#c5c0ff'
  secondary: '#5e5e63'
  on-secondary: '#ffffff'
  secondary-container: '#e4e1e8'
  on-secondary-container: '#646469'
  tertiary: '#414347'
  on-tertiary: '#ffffff'
  tertiary-container: '#585a5e'
  on-tertiary-container: '#d1d1d6'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e3dfff'
  primary-fixed-dim: '#c5c0ff'
  on-primary-fixed: '#140067'
  on-primary-fixed-variant: '#3f35a3'
  secondary-fixed: '#e4e1e8'
  secondary-fixed-dim: '#c8c5cc'
  on-secondary-fixed: '#1b1b20'
  on-secondary-fixed-variant: '#46464c'
  tertiary-fixed: '#e2e2e7'
  tertiary-fixed-dim: '#c6c6cb'
  on-tertiary-fixed: '#1a1c1f'
  on-tertiary-fixed-variant: '#45474b'
  background: '#f9f9ff'
  on-background: '#151c27'
  surface-variant: '#dce2f3'
typography:
  display-hero:
    fontFamily: Geist
    fontSize: 40px
    fontWeight: '600'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Geist
    fontSize: 30px
    fontWeight: '600'
    lineHeight: 38px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 32px
  body-lg:
    fontFamily: Geist
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  headline-lg-mobile:
    fontFamily: Geist
    fontSize: 26px
    fontWeight: '600'
    lineHeight: 32px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 64px
  container-max: 1200px
  auth-card-width: 440px
---

## Brand & Style

The visual identity of this design system centers on technical precision and calm reliability. It is engineered for a high-performance operations environment where speed and clarity are paramount. The brand personality is professional and authoritative, yet the "hero" entry points—specifically login and signup flows—introduce an inviting, high-fidelity warmth to humanize the data-driven core.

The design style follows a **Modern Corporate** aesthetic with **Minimalist** influences. It prioritizes functional density and legibility while utilizing sophisticated background treatments—such as soft mesh gradients in violet and cool slates or mathematical geometric patterns—to create a sense of "premium engineering" during the authentication experience. The interface should feel like a precision instrument: lightweight, responsive, and trustworthy.

## Colors

The palette is anchored by a deep violet primary accent, representing intelligence and operational focus. 

- **Primary (#534AB7):** Used for critical actions, active states, and brand-defining moments.
- **Secondary (#2D2D32):** A deep charcoal for primary text and high-contrast iconography, ensuring maximum readability.
- **Surface & Backgrounds:** The base is a clean, neutral white (#FFFFFF). Subtle shifts to off-white or very light lavender (#F9F9FF) are used to differentiate container levels.
- **Auth Hero Gradients:** For login and signup screens, a subtle linear gradient is employed: `Linear (Top-Left to Bottom-Right) #FDFDFF to #EEECFB`. This provides the "high-fidelity" depth requested without compromising the professional tone.

## Typography

This design system utilizes the **Geist** typeface family across all levels to maintain a clean, technical, and developer-centric feel. Geist’s monospaced-adjacent proportions provide excellent alignment for operational data.

- **Display & Headlines:** Use tighter letter-spacing and medium-to-semibold weights to command attention on auth screens.
- **Body Text:** Standard weight for maximum readability. Line heights are generous (1.5x) to ensure the UI feels calm and spacious.
- **Labels:** Used for form headers and button text, often utilizing a slightly heavier weight to distinguish them from flowable text.

## Layout & Spacing

The system employs a **Fixed Grid** logic for core content and a **Centered Hero** layout for authentication flows.

- **Grid System:** A 12-column grid with 24px gutters is standard for internal dashboards.
- **Auth Layout:** For login and signup, the interface uses a single-column layout centered both vertically and horizontally. The primary interaction card is fixed at 440px to ensure a focused, efficient user journey.
- **Spacing Rhythm:** Based on a 4px baseline. Most components use 16px (md) or 24px (lg) padding to maintain an open, inviting feel while remaining compact enough for professional use.
- **Responsive Behavior:** On mobile, margins reduce to 16px, and the auth card expands to fill the viewport width, maintaining the central focus.

## Elevation & Depth

Visual hierarchy is established through **Tonal Layers** and **Low-Contrast Outlines**.

- **Surfaces:** Main backgrounds are flat. Interactive cards (like the login box) use a white fill with a very subtle 1px border (#E5E7EB) to define their boundaries.
- **Shadows:** Avoid heavy, muddy shadows. Use a single "Soft Lift" shadow for the primary auth card: `0px 4px 20px rgba(83, 74, 183, 0.06)`. This subtle violet tint links the elevation back to the brand color.
- **Backdrop:** On login screens, the background uses a subtle geometric overlay (dots or thin lines) at 5% opacity to provide a sense of technical depth without distracting from the form.

## Shapes

The shape language is **Soft** and precise. 

- **Components:** Buttons, input fields, and cards utilize a 0.25rem (4px) or 0.5rem (8px) corner radius. This provides a modern, approachable feel while retaining the structural "grid-aligned" look suitable for an operations tool.
- **Feedback Elements:** Small chips or status indicators may use a slightly more rounded 12px radius to differentiate them from structural input elements.

## Components

- **Buttons:** 
  - *Primary:* Solid #534AB7 fill with white Geist Semibold text. No gradient on the button itself to keep it feeling "fast."
  - *Secondary:* Ghost style with a #E5E7EB border and #2D2D32 text.
- **Input Fields:** 
  - Default: 1px border in #D1D5DB. 
  - Focused: 1px border in #534AB7 with a 2px outer "glow" (alpha-transparent violet).
  - Labels: Geist Label-md, positioned strictly above the field.
- **Auth Cards:** White background, 24px or 32px internal padding, 8px corner radius.
- **Chips/Badges:** Used for small indicators (e.g., "New Feature" or "Beta"). These should be low-contrast (e.g., Light Violet background with Dark Violet text).
- **Checkboxes:** Square with a 2px radius, filling with #534AB7 when active.
- **Progress Indicators:** A thin, high-contrast violet bar at the top of the screen or card during signup transitions to signal speed and system responsiveness.