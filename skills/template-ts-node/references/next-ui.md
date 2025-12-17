# React/Next.js UI Projects

Set up React/Next.js UI projects with modern tooling and best practices.

## Additional Dependencies

### Production Dependencies

```json
{
  "react": "^19",
  "react-dom": "^19",
  "next": "^16",
  "tailwindcss": "^4",
  "tailwind-merge": "latest",
  "tailwind-variants": "latest",
  "lucide-react": "latest",
  "next-intl": "latest"
}
```

Install core UI dependencies:

```bash
bun add react@^19 react-dom@^19 next@^16
```

Install Tailwind CSS v4 and utilities:

```bash
bun add tailwindcss@^4 tailwind-merge tailwind-variants
```

Add icons and internationalization:

```bash
bun add lucide-react
bun add next-intl  # Optional, for i18n support
```

### Development Dependencies

```json
{
  "@types/react": "^19",
  "@types/react-dom": "^19",
  "@tailwindcss/postcss": "latest"
}
```

Install type definitions:

```bash
bun add -D @types/react @types/react-dom
```

Install Tailwind PostCSS plugin:

```bash
bun add -D @tailwindcss/postcss
```

## Biome Configuration

Extend Biome config with React and Next.js presets:

```jsonc
{
  "$schema": "https://biomejs.dev/schemas/1.9.4/schema.json",
  "extends": [
    "ultracite/core",
    "ultracite/react",
    "ultracite/next",
    "@sablier/devkit/biome/base",
    "@sablier/devkit/biome/ui"
  ]
}
```

Key configurations from React/Next.js presets:

- JSX formatting and linting rules
- React hooks validation
- Next.js-specific patterns (e.g., Image component usage)
- Accessibility rules for UI components

## TypeScript Configuration

Use Next.js-specific TypeScript config instead of base Node config:

```json
{
  "extends": "./node_modules/@sablier/devkit/tsconfig/next.json",
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": [
    "next-env.d.ts",
    "**/*.ts",
    "**/*.tsx",
    ".next/types/**/*.ts"
  ],
  "exclude": [
    "node_modules"
  ]
}
```

The Next.js config includes:

- JSX preservation for React
- Module resolution for App Router
- Incremental compilation
- Strict type checking

## Project Structure

```
project/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   ├── globals.css        # Global styles with Tailwind
│   └── [route]/           # Dynamic routes
│       ├── layout.tsx
│       └── page.tsx
├── ui/                     # Reusable UI components
│   ├── button.tsx
│   ├── card.tsx
│   └── index.ts           # Barrel exports
├── lib/                    # Utilities and helpers
│   ├── utils.ts           # Tailwind merge, cn() helper
│   └── constants.ts
├── public/                 # Static assets
│   ├── images/
│   └── fonts/
├── i18n/                   # Internationalization (optional)
│   ├── messages/
│   │   ├── en.json
│   │   └── es.json
│   └── config.ts
├── postcss.config.js       # PostCSS with Tailwind
├── tailwind.config.ts      # Tailwind configuration
└── next.config.ts          # Next.js configuration
```

### Directory Conventions

**app/**: Use Next.js App Router conventions. Each route contains `page.tsx` (default export) and optional `layout.tsx`, `loading.tsx`, `error.tsx`.

**ui/**: Store reusable components. Use named exports. Create an `index.ts` for barrel exports:

```tsx
export { Button } from "./button";
export { Card } from "./card";
```

**lib/**: Place utility functions, constants, and shared logic. Keep components out of this directory.

**public/**: Serve static files directly. Reference with `/images/logo.png` in code.

**i18n/**: Organize translations by locale. Use `next-intl` for internationalization.

## Tailwind CSS v4 Setup

### PostCSS Configuration

Create `postcss.config.js`:

```js
export default {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
```

Tailwind v4 uses PostCSS instead of direct configuration. The plugin handles compilation automatically.

### CSS Entry Point

Create `app/globals.css`:

```css
@import "tailwindcss";

/* Custom base styles */
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 0 0% 3.9%;
  }

  .dark {
    --background: 0 0% 3.9%;
    --foreground: 0 0% 98%;
  }
}

/* Custom components */
@layer components {
  .container {
    @apply mx-auto px-4;
  }
}
```

Import in `app/layout.tsx`:

```tsx
import "./globals.css";
```

### Tailwind Configuration (Optional)

For custom theme extensions, create `tailwind.config.ts`:

```ts
import type { Config } from "tailwindcss";

export default {
  content: [
    "./app/**/*.{ts,tsx}",
    "./ui/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f9ff",
          // ... custom color palette
        },
      },
    },
  },
} satisfies Config;
```

### Utility Helper

Create `lib/utils.ts` for class name merging:

```ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

Use in components:

```tsx
<div className={cn("base-class", conditionalClass && "active")} />
```

## Next.js Configuration

Create `next.config.ts`:

```ts
import type { NextConfig } from "next";

const config: NextConfig = {
  reactStrictMode: true,
  experimental: {
    reactCompiler: true,  // Enable React Compiler for auto-memoization
  },
  images: {
    formats: ["image/webp"],  // Use WebP for optimized images
  },
};

export default config;
```

### Key Settings

**reactStrictMode**: Enable strict mode to catch common bugs during development.

**reactCompiler**: Automatically optimize component re-renders without manual `useMemo`/`useCallback`. Requires React 19+.

**images.formats**: Use WebP format for automatic image optimization. Next.js Image component handles conversion.

### Environment Variables

Create `.env.local` for local development:

```env
NEXT_PUBLIC_API_URL=http://localhost:3000/api
DATABASE_URL=postgresql://...
```

Access public variables in client components:

```tsx
const apiUrl = process.env.NEXT_PUBLIC_API_URL;
```

Access private variables in Server Components or API routes:

```tsx
const dbUrl = process.env.DATABASE_URL;
```

## Component Patterns

### Server Components (Default)

Use Server Components by default for better performance:

```tsx
// ui/card.tsx
export function Card({ title, children }: CardProps) {
  return (
    <div className="rounded-lg border p-4">
      <h3 className="font-semibold">{title}</h3>
      {children}
    </div>
  );
}
```

Server Components can:

- Fetch data directly
- Access backend resources
- Keep sensitive logic on server
- Reduce client bundle size

### Client Components

Add `"use client"` directive for interactivity:

```tsx
// ui/button.tsx
"use client";

import { useState } from "react";

export function Button({ onClick, children }: ButtonProps) {
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    setLoading(true);
    await onClick();
    setLoading(false);
  };

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className="px-4 py-2 bg-blue-600 text-white rounded"
    >
      {loading ? "Loading..." : children}
    </button>
  );
}
```

Use Client Components when you need:

- Event handlers (onClick, onChange)
- React hooks (useState, useEffect)
- Browser APIs (localStorage, window)

### Component Variants with tailwind-variants

Use `tv()` from tailwind-variants for type-safe variant styling:

```tsx
// ui/button.tsx
"use client";

import { tv, type VariantProps } from "tailwind-variants";

const button = tv({
  base: "font-medium rounded-lg transition-colors",
  variants: {
    intent: {
      primary: "bg-blue-600 text-white hover:bg-blue-700",
      secondary: "bg-gray-200 text-gray-900 hover:bg-gray-300",
      danger: "bg-red-600 text-white hover:bg-red-700",
    },
    size: {
      sm: "px-3 py-1.5 text-sm",
      md: "px-4 py-2 text-base",
      lg: "px-6 py-3 text-lg",
    },
    disabled: {
      true: "opacity-50 cursor-not-allowed",
    },
  },
  defaultVariants: {
    intent: "primary",
    size: "md",
  },
});

type ButtonProps = VariantProps<typeof button> & {
  children: React.ReactNode;
  onClick?: () => void;
};

export function Button({ intent, size, disabled, children, onClick }: ButtonProps) {
  return (
    <button
      className={button({ intent, size, disabled })}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
}
```

Usage:

```tsx
<Button intent="primary" size="lg">Click me</Button>
<Button intent="danger" disabled>Delete</Button>
```

### Export Conventions

Use named exports for components:

```tsx
export function Header() { /* ... */ }
export function Footer() { /* ... */ }
```

Exception: `page.tsx` files require default export:

```tsx
// app/page.tsx
export default function HomePage() {
  return <div>Home</div>;
}
```

Layout files can use either:

```tsx
// app/layout.tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

## Icon Usage

Use lucide-react for consistent iconography:

```tsx
import { Search, ChevronRight, User } from "lucide-react";

export function SearchButton() {
  return (
    <button className="flex items-center gap-2">
      <Search className="w-4 h-4" />
      <span>Search</span>
    </button>
  );
}
```

Icons support:

- Size via className: `className="w-5 h-5"`
- Color via className: `className="text-blue-600"`
- Stroke width: `strokeWidth={2}`

## Internationalization (Optional)

Set up next-intl for i18n support:

```tsx
// i18n/config.ts
export const locales = ["en", "es"] as const;
export const defaultLocale = "en" as const;
```

```json
// i18n/messages/en.json
{
  "common": {
    "welcome": "Welcome to our app",
    "login": "Log in"
  }
}
```

Use in components:

```tsx
import { useTranslations } from "next-intl";

export function Welcome() {
  const t = useTranslations("common");
  return <h1>{t("welcome")}</h1>;
}
```

Configure in `app/[locale]/layout.tsx` for locale-based routing.
