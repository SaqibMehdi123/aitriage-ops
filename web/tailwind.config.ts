import type { Config } from "tailwindcss";

/**
 * "Precision Operations" design system (from the Stitch design folder's
 * DESIGN.md). Colours, type scale, spacing, and radii are mirrored here so the
 * React components match the supplied screen templates 1:1.
 */
const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#3b309e",
        "primary-container": "#534ab7",
        "on-primary": "#ffffff",
        "on-primary-container": "#d1ccff",
        "primary-fixed": "#e3dfff",
        "primary-fixed-dim": "#c5c0ff",
        "on-primary-fixed": "#140067",
        "on-primary-fixed-variant": "#3f35a3",
        "inverse-primary": "#c5c0ff",
        secondary: "#4648d4",
        "secondary-container": "#6063ee",
        "on-secondary": "#ffffff",
        "on-secondary-container": "#fffbff",
        "secondary-fixed": "#e1e0ff",
        "secondary-fixed-dim": "#c0c1ff",
        "on-secondary-fixed": "#07006c",
        "on-secondary-fixed-variant": "#2f2ebe",
        tertiary: "#683500",
        "tertiary-container": "#8a4900",
        "on-tertiary": "#ffffff",
        "on-tertiary-container": "#ffc69a",
        "tertiary-fixed": "#ffdcc3",
        "tertiary-fixed-dim": "#ffb77d",
        "on-tertiary-fixed": "#2f1500",
        "on-tertiary-fixed-variant": "#6e3900",
        error: "#ba1a1a",
        "on-error": "#ffffff",
        "error-container": "#ffdad6",
        "on-error-container": "#93000a",
        background: "#f9f9ff",
        "on-background": "#151c27",
        surface: "#f9f9ff",
        "surface-dim": "#d3daea",
        "surface-bright": "#f9f9ff",
        "surface-container-lowest": "#ffffff",
        "surface-container-low": "#f0f3ff",
        "surface-container": "#e7eefe",
        "surface-container-high": "#e2e8f8",
        "surface-container-highest": "#dce2f3",
        "surface-variant": "#dce2f3",
        "on-surface": "#151c27",
        "on-surface-variant": "#474553",
        "inverse-surface": "#2a313d",
        "inverse-on-surface": "#ebf1ff",
        outline: "#787584",
        "outline-variant": "#c8c4d5",
        "surface-tint": "#584fbc",
      },
      fontFamily: {
        sans: ["Geist", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      fontSize: {
        "display-lg": ["32px", { lineHeight: "40px", letterSpacing: "-0.02em", fontWeight: "600" }],
        "headline-md": ["24px", { lineHeight: "32px", letterSpacing: "-0.01em", fontWeight: "600" }],
        "headline-sm": ["20px", { lineHeight: "28px", fontWeight: "600" }],
        "title-lg": ["18px", { lineHeight: "26px", fontWeight: "500" }],
        "body-md": ["16px", { lineHeight: "24px", fontWeight: "400" }],
        "body-sm": ["14px", { lineHeight: "20px", fontWeight: "400" }],
        "label-md": ["13px", { lineHeight: "18px", letterSpacing: "0.01em", fontWeight: "500" }],
        "label-sm": ["12px", { lineHeight: "16px", fontWeight: "600" }],
        code: ["13px", { lineHeight: "20px", fontWeight: "400" }],
      },
      spacing: {
        unit: "4px",
        xs: "4px",
        sm: "8px",
        md: "16px",
        lg: "24px",
        xl: "32px",
        gutter: "20px",
        "margin-mobile": "16px",
        "margin-desktop": "32px",
      },
      borderRadius: {
        DEFAULT: "0.375rem",
        sm: "0.125rem",
        md: "0.375rem",
        lg: "0.5rem",
        xl: "0.75rem",
        full: "9999px",
      },
      maxWidth: {
        "container-max": "1440px",
      },
      boxShadow: {
        // Level 2 (dropdowns/modals) from DESIGN.md — subtle, diffused.
        elevated:
          "0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05)",
      },
    },
  },
  plugins: [],
};

export default config;
