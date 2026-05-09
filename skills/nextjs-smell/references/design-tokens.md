# Design Tokens & Component Variants

For smells D1–D8, S1–S3. The thread connecting these: tokens exist, components
should consume them — not hardcode their own values.

## The token hierarchy

```
Primitive tokens   →   Semantic tokens   →   Component tokens
(raw values)           (intent-named)        (component-scoped)

#0a0a0a               background.default     button.primary.bg
12px                  spacing.xs             card.padding
"Inter, sans"         font.body              heading.font
```

A button shouldn't reference `#0a0a0a` directly (D1). It should reference
`var(--button-primary-bg)` or `theme.button.primary.bg`, which references
`semantic.background.brand`, which references `primitive.color.slate.950`.
This is what makes a rebrand a config change instead of a search-and-replace.

## Tailwind v4 — CSS-first config

Tailwind v4 moved config into CSS via `@theme`:

```css
/* app/globals.css */
@import "tailwindcss";

@theme {
  --color-bg: oklch(0.98 0 0);
  --color-fg: oklch(0.18 0 0);
  --color-brand: oklch(0.6 0.2 260);
  --spacing: 0.25rem;          /* base; spacing-1 = 0.25rem, -2 = 0.5rem ... */
  --font-display: "Inter", sans-serif;
  --radius: 0.5rem;
}

@media (prefers-color-scheme: dark) {
  @theme {
    --color-bg: oklch(0.12 0 0);
    --color-fg: oklch(0.96 0 0);
  }
}
```

This makes every utility (`bg-brand`, `text-fg`, `p-4`) resolve to a token. A
component using `bg-[#0a0a0a]` (D1) bypasses this — and won't reflect a token
change.

## Variants done right (D4)

For a `Button` with multiple variants, don't pile on booleans:

```tsx
// ❌ D4 boolean explosion
<Button primary danger small disabled outline rounded>...</Button>
// 6 booleans = 64 combinations, half nonsense
```

Use `class-variance-authority` (cva) — typed variants with one source of truth:

```tsx
import {cva, type VariantProps} from "class-variance-authority";

const button = cva(
  "inline-flex items-center justify-center font-medium transition focus-visible:outline-2",
  {
    variants: {
      intent: {
        primary: "bg-brand text-white hover:bg-brand/90",
        secondary: "bg-muted text-fg hover:bg-muted/80",
        danger: "bg-red-600 text-white hover:bg-red-500",
        ghost: "bg-transparent hover:bg-muted",
      },
      size: {
        sm: "h-8 px-3 text-sm",
        md: "h-10 px-4",
        lg: "h-12 px-6 text-lg",
      },
      shape: {
        rect: "rounded",
        pill: "rounded-full",
      },
    },
    defaultVariants: {intent: "primary", size: "md", shape: "rect"},
  }
);

type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & VariantProps<typeof button>;

export function Button({intent, size, shape, className, ...rest}: Props) {
  return <button className={button({intent, size, shape, className})} {...rest} />;
}
```

Now `Button`'s API is three named enums, types enforce valid combinations, and
the design rule lives in one place.

## Tokens via CSS variables (vanilla / shadcn-style)

```css
:root {
  --background: 0 0% 100%;
  --foreground: 0 0% 4%;
  --primary: 240 100% 50%;
  --primary-foreground: 0 0% 100%;
}
.dark {
  --background: 0 0% 4%;
  --foreground: 0 0% 96%;
}
```

```css
/* Then in component CSS */
.btn-primary {
  background: hsl(var(--primary));
  color: hsl(var(--primary-foreground));
}
```

shadcn/ui uses this approach — zero runtime, supports dark mode via class, and
works with both Tailwind utilities and component CSS.

## Spacing scale (D3)

Pick a scale, stick to it. Tailwind's default (4px base, 1=4, 2=8, 3=12, 4=16…)
is fine. Outliers like `mt-[7px]` (D3) are almost always either:
- a bug in the design (the spec says 8, not 7), or
- a one-off that should become a documented exception.

Audit cue: grep for `\[\d+px\]` or `\[0\.\d+rem\]` in JSX. Each hit needs
justification.

## Z-index scale (S2)

Don't `z-[9999]`. Define a scale up front:

```css
@theme {
  --z-dropdown: 1000;
  --z-sticky: 1020;
  --z-modal-backdrop: 1040;
  --z-modal: 1050;
  --z-popover: 1060;
  --z-tooltip: 1070;
  --z-toast: 1080;
}
```

Five layers handle most apps. If you need more, you have a layering problem,
not a z-index problem.

## Dark mode (D6)

Tokens make dark mode trivial — the *same* utilities (`bg-bg`, `text-fg`) work
in both, because the token re-resolves under `.dark`. The smell is when half
the codebase uses tokens and half uses `bg-white text-black` (which doesn't
swap), so a "toggle dark mode" button only flips the parts that knew to opt in.

## Detection cues for the audit

| Smell | grep / scan for |
|---|---|
| D1 | `#[0-9a-fA-F]{3,8}\b`, `rgb\(`, `rgba\(` in `*.tsx` |
| D2 | JSX `className=` strings >120 chars OR repeated >3× across files |
| D3 | `\[\d+(px\|rem)\]` outside design system internals |
| D5 | multiple import paths to component with same export name |
| D6 | files with `bg-white\|text-black\|bg-gray-` and no `dark:` partner |
| D7 | `@media \(max-width: \d{3,4}px\)` outside config |
| D8 | `style={{ ?(margin\|padding\|color\|fontSize)` for static values |
| S1 | `!important` count per file |
| S2 | `z-(index)?:.*[3-9]\d{2,}` (z > 199 with no scale) |
| S3 | `-webkit-`, `-moz-` for autoprefixable properties |

## Minimum viable design-system audit

If you only have 30 minutes:

1. Grep raw hex/rgb in JSX → list violators.
2. Check Tailwind config / CSS vars: do tokens exist and have decent names?
3. Pick three components (button, input, card). Read them. Are they consuming
   tokens?
4. Open the app in dev, switch to dark mode (if supported). Where does it
   break?
5. Run Knip — duplicate component imports (D5) often show as unused exports.