---
name: tailwind-css
description: Tailwind CSS v4 configuration and theming reference. Use when working with styling, CSS, Tailwind utilities, design tokens, colors, breakpoints, spacing, typography, custom utilities, or theme customization. Covers CSS-only configuration (no tailwind.config.ts), @theme directive, and custom variants.
---

# Tailwind CSS v4

## Purpose

Reference for Tailwind CSS v4 theme system and CSS-only configuration. Use this when working with styles, design tokens, or custom utilities.

## Critical: Tailwind v4 Differences

**No `tailwind.config.ts` file exists.** Tailwind CSS v4 uses **CSS-only configuration**.

All theme customization is done via CSS files using:
- `@theme static` - Define design tokens
- `@utility` - Create custom utilities
- `@custom-variant` - Define responsive variants
- `@layer` - Control CSS cascade order

## Tailwind v4 Breaking Changes

**Renamed Classes:**

- `bg-gradient-to-*` → `bg-linear-to-*` (all gradient directions)
  - `bg-gradient-to-r` → `bg-linear-to-r`
  - `bg-gradient-to-t` → `bg-linear-to-t`
  - `bg-gradient-to-br` → `bg-linear-to-br`
  - etc. (applies to all 8 directions)

**CSS Variable Syntax:**

- `bg-[--custom-var]` → `bg-(--custom-var)` (parentheses instead of square brackets)

**Shorter Aliases:**

- `flex-shrink-0` → Use `shrink-0` (shorter equivalent)

**Property Conflicts:**

- `focus-visible:outline-2` conflicts with `focus-visible:outline` (same CSS properties)
  - Use only one, typically combine as: `focus-visible:outline-2 focus-visible:outline-offset-2`

## Theme Files

### `index.css` - Orchestrator
- Defines layer order: `@layer theme, base, utilities`
- Imports Tailwind core + all custom files
- Entry point for entire theme system

### `theme.css` - Design Tokens
Core design system defined with `@theme static`:

**Colors:**
Define your color palette with semantic naming:
```css
@theme static {
  --color-primary-*: ...;
  --color-secondary-*: ...;
  --color-neutral-*: ...;
  --color-background-*: ...;
  --color-text-*: ...;
  --color-border-*: ...;
}
```

**Breakpoints:**
Define custom breakpoints as needed:
```css
@theme static {
  --breakpoint-xs: 480px;
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;
}
```

**Typography:**
Define font families, sizes, and weights:
```css
@theme static {
  --font-sans: "Inter", system-ui, sans-serif;
  --font-mono: "Fira Code", monospace;
}
```

**Spacing:**
Define spacing scales, container widths, border radii, z-index values, etc.

### `base.css` - CSS Resets
- Removes default link underlines
- Resets button borders and font
- Normalizes text element margins

### `utilities.css` - Custom Utilities
Define custom utilities with `@utility`:

**Layout Examples:**
```css
@utility column {
  display: flex;
  flex-direction: column;
}

@utility container-custom {
  width: 100%;
  max-width: var(--breakpoint-xl);
  margin: 0 auto;
}
```

**Animation Examples:**
```css
@utility slide-up-fade-in {
  animation: slideUpFadeIn 0.3s ease-out;
}

@keyframes slideUpFadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
```

### `variants.css` - Custom Variants
Responsive variants via `@custom-variant`:

- Max-width: `max-xxs:`, `max-xs:`, `max-sm:`, etc.
- Min-width: `min-xxs:`, `min-xs:`, `min-sm:`, etc.
- Between: `between-xs-sm:`, `between-sm-md:`, etc.

## Usage Patterns

### Design Tokens (Preferred)
```tsx
// Use theme colors
<div className="bg-primary-100 text-neutral-400 border-border-primary">

// Use custom breakpoints
<div className="hidden lg:block between-sm-md:flex">

// Use theme spacing
<div className="container mx-auto px-4 lg:px-8">
```

### Custom Utilities
```tsx
// Layout utilities
<div className="column gap-4">
<div className="row items-center">
<div className="container-custom">

// Custom typography utilities
<p className="text-custom-large text-neutral-300">
```

### Component-Specific Styles
For complex animations or component-specific styles, use **CSS Modules**:

```tsx
// component.module.css
@keyframes customAnimation { /* ... */ }

.component {
  animation: customAnimation 1s ease;
}
```

### Modern CSS Features
Theme uses modern CSS syntax:
```css
/* Relative color syntax */
background: rgb(from var(--color-primary) r g b / 0.08);

/* CSS custom properties */
color: var(--color-text-primary);
```

## Integration with tailwind-variants

Use `tv()` for component variants with theme tokens:

```typescript
import { tv } from "tailwind-variants";

const button = tv({
  base: "row items-center gap-2 transition-colors",
  variants: {
    variant: {
      primary: "bg-primary text-white hover:bg-primary-dark",
      secondary: "bg-secondary text-neutral-100 hover:bg-secondary-dark",
    },
  },
});
```

## Best Practices

✅ **Use theme tokens** - No arbitrary values unless absolutely necessary
✅ **Reference existing utilities** - Check `utilities.css` for available helpers
✅ **Use custom breakpoints** - Leverage your project's responsive system
✅ **CSS Modules for complex styles** - Keep utility classes simple
✅ **Semantic color names** - Use `background-*`, `text-*`, `border-*` for consistency

❌ **Don't create `tailwind.config.ts`** - All config is CSS-based in v4
❌ **Don't use arbitrary values excessively** - Maintain design system consistency
❌ **Don't hardcode colors** - Use theme tokens

## Quick Reference

**Config Method:** CSS files with `@theme`, `@utility`, `@custom-variant`
**No JS Config:** No `tailwind.config.ts` file exists or needed in v4
**Theme Definition:** Use `@theme static` directive in CSS files
**Custom Utilities:** Use `@utility` directive
**Custom Variants:** Use `@custom-variant` directive
