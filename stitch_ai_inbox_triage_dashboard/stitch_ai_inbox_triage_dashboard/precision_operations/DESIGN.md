---
name: Precision Operations
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
  secondary: '#4648d4'
  on-secondary: '#ffffff'
  secondary-container: '#6063ee'
  on-secondary-container: '#fffbff'
  tertiary: '#683500'
  on-tertiary: '#ffffff'
  tertiary-container: '#8a4900'
  on-tertiary-container: '#ffc69a'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e3dfff'
  primary-fixed-dim: '#c5c0ff'
  on-primary-fixed: '#140067'
  on-primary-fixed-variant: '#3f35a3'
  secondary-fixed: '#e1e0ff'
  secondary-fixed-dim: '#c0c1ff'
  on-secondary-fixed: '#07006c'
  on-secondary-fixed-variant: '#2f2ebe'
  tertiary-fixed: '#ffdcc3'
  tertiary-fixed-dim: '#ffb77d'
  on-tertiary-fixed: '#2f1500'
  on-tertiary-fixed-variant: '#6e3900'
  background: '#f9f9ff'
  on-background: '#151c27'
  surface-variant: '#dce2f3'
typography:
  display-lg:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Geist
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  title-lg:
    fontFamily: Geist
    fontSize: 18px
    fontWeight: '500'
    lineHeight: 26px
  body-md:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Geist
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
  code:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  container-max: 1440px
  gutter: 20px
  margin-mobile: 16px
  margin-desktop: 32px
---

## Brand & Style

This design system is engineered for high-velocity operations and support leads who manage complex AI-driven workflows. The brand personality is **composed, efficient, and transparent**, prioritizing clarity of information over visual decoration. 

The aesthetic is a refined **Modern Corporate** style with a focus on **Minimalism**. It utilizes a "light-first" philosophy to reduce cognitive load during long sessions. High-density data is balanced by generous whitespace and a strict adherence to a single-accent color strategy to draw attention only where action is required. The emotional response should be one of complete control and professional reliability.

## Colors

The palette is anchored by a near-white background to provide a clean canvas for data. 
- **Primary Violet (#534AB7):** Reserved strictly for primary actions, active navigation states, and critical brand touchpoints.
- **Surface & Background:** Use `#F9FAFB` for the main canvas and `#FFFFFF` for elevated containers (cards, sidebars) to create subtle depth.
- **Borders:** A consistent `#E5E7EB` is used for structural separation.
- **Semantic Colors:** Use low-saturation greens, ambers, and reds for status indicators to ensure they do not compete with the primary violet accent.

## Typography

The typography system uses **Geist** for its technical precision and exceptional legibility in data-heavy environments. 
- **Scale:** A tight scale ensures that even with significant information density, the hierarchy remains obvious.
- **Contrast:** Use font weight (Medium/SemiBold) rather than color shifts to indicate importance.
- **Data:** For rule builders or AI logs, use **JetBrains Mono** to distinguish machine-generated content from UI labels.
- **Mobile:** Scale `display-lg` down to 24px (`headline-md`) for mobile viewports to maintain readability without excessive scrolling.

## Layout & Spacing

The layout follows a **Fixed Grid** philosophy on desktop to maintain a professional, organized dashboard feel, transitioning to a fluid model on smaller devices.
- **Desktop (1440px+):** 12-column grid with a fixed sidebar (256px). Main content area uses 32px margins.
- **Tablet (768px - 1439px):** Sidebar collapses to icons or a drawer. Margins reduce to 24px.
- **Mobile (<768px):** Single column flow. Margins reduce to 16px.
- **Rhythm:** Use an 8px base grid for all component dimensions and a 4px increment for tight internal spacing (e.g., icon to text).

## Elevation & Depth

This design system avoids heavy drop shadows to maintain a "flat-plus" aesthetic. Depth is communicated through **Tonal Layering** and **Low-Contrast Outlines**.
- **Level 0 (Background):** `#F9FAFB` - The base canvas.
- **Level 1 (Cards/Sidebar):** `#FFFFFF` with a 1px border of `#E5E7EB`. No shadow.
- **Level 2 (Dropdowns/Modals):** `#FFFFFF` with a 1px border and a very subtle, diffused shadow: `0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05)`.
- **Interactions:** Hover states on interactive rows should use a subtle background shift to `#F3F4F6` rather than an elevation increase.

## Shapes

The shape language is **Soft and Precise**. 
- **Standard Radius:** 6px (0.375rem) for buttons, input fields, and small cards. This offers a modern feel without looking "bubbly."
- **Large Radius:** 8px (0.5rem) for main dashboard containers and modals.
- **Full Radius:** Reserved exclusively for status chips (pills) and user avatars to provide a distinct visual category for metadata.

## Components

- **Buttons:** Primary buttons use the Violet accent with white text. Secondary buttons use a white background with a 1px `#D1D5DB` border and dark text. Flat ghost buttons are used for utility actions.
- **Data Tables:** Use a "zebra-less" design. Separate rows with 1px horizontal lines (`#F3F4F6`). Header text should be `label-sm` with a subtle grey color.
- **Status Chips:** Small, pill-shaped indicators. Use a light background (10% opacity of the color) and a dark foreground text for high legibility (e.g., Success = Light Green BG / Dark Green Text).
- **Rule Builders:** Horizontal stack of select inputs and "and/or" toggles. Use a distinct vertical "connector line" on the left to group nested logic.
- **Sidebar:** Darker text on the `#FFFFFF` surface. The active state is indicated by a 2px vertical Violet bar on the left edge and a subtle Violet-tinted background shift.
- **Input Fields:** 1px border with a 2px Violet ring on focus. Use `body-sm` for input text to maximize space in dense forms.