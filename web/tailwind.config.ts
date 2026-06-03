import type { Config } from "tailwindcss";

/**
 * "Graphite + Amber" — warm neutral grays (stone) with an amber accent.
 * Semantic tokens drive the whole app, so the entire UI follows this palette.
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
        // Amber — primary accent / CTAs
        primary: "#b45309",
        "primary-container": "#92400e",
        "on-primary": "#ffffff",
        "on-primary-container": "#ffffff",
        "primary-fixed": "#fef3c7",
        "primary-fixed-dim": "#fcd34d",
        "on-primary-fixed": "#78350f",
        "on-primary-fixed-variant": "#92400e",
        "inverse-primary": "#fcd34d",
        // Graphite — secondary / neutral accents
        secondary: "#57534e",
        "secondary-container": "#e7e5e4",
        "on-secondary": "#ffffff",
        "on-secondary-container": "#292524",
        "secondary-fixed": "#e7e5e4",
        "secondary-fixed-dim": "#d6d3d1",
        "on-secondary-fixed": "#1c1917",
        "on-secondary-fixed-variant": "#44403c",
        // Teal — tertiary (for chart/chip variety)
        tertiary: "#0f766e",
        "tertiary-container": "#99f6e4",
        "on-tertiary": "#ffffff",
        "on-tertiary-container": "#134e4a",
        "tertiary-fixed": "#ccfbf1",
        "tertiary-fixed-dim": "#5eead4",
        "on-tertiary-fixed": "#134e4a",
        "on-tertiary-fixed-variant": "#115e59",
        // Error
        error: "#dc2626",
        "on-error": "#ffffff",
        "error-container": "#fee2e2",
        "on-error-container": "#991b1b",
        // Neutral surfaces (stone)
        background: "#fafaf9",
        "on-background": "#1c1917",
        surface: "#fafaf9",
        "surface-dim": "#e7e5e4",
        "surface-bright": "#ffffff",
        "surface-container-lowest": "#ffffff",
        "surface-container-low": "#f5f5f4",
        "surface-container": "#efedec",
        "surface-container-high": "#e7e5e4",
        "surface-container-highest": "#dedddb",
        "surface-variant": "#e7e5e4",
        "on-surface": "#1c1917",
        "on-surface-variant": "#57534e",
        "inverse-surface": "#292524",
        "inverse-on-surface": "#fafaf9",
        outline: "#a8a29e",
        "outline-variant": "#e7e5e4",
        "surface-tint": "#b45309",
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
        elevated:
          "0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05)",
      },
    },
  },
  plugins: [],
};

export default config;
