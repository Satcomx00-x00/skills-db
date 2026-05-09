# A11y Checklist

For smells A1–A9. Automated tools catch ~30–40% of WCAG issues — the rest needs
keyboard testing, screen reader testing, and judgment. This file calibrates
both halves.

## What automation catches (and what it doesn't)

| Tool | Static / runtime | Catches | Misses |
|---|---|---|---|
| `eslint-plugin-jsx-a11y` | static | A1 (button no name), A2 (click on div), A3 (label-for), A7 (alt) | logical reading order, focus return, naming quality |
| Biome a11y group | static | similar to jsx-a11y | similar |
| **axe-core** (Playwright/Cypress integration) | runtime | colour contrast, ARIA validity, role/state mismatches | keyboard traps, focus order in flows |
| `pa11y` / `pa11y-ci` | runtime (HTML CodeSniffer or axe) | same as axe runtime, plus broader rule sets | as above |
| Lighthouse | runtime | accessibility score (subset of axe rules) | flow-level issues |

**Rule of thumb:** if all three of "lint clean, axe clean, Lighthouse 100" are
true, you're at ~40%. Manual keyboard pass + one screen reader spot-check is
worth more than any single tool.

## CLI quick-reference

```bash
# axe via Playwright (recommended for dev workflows)
npm i -D @axe-core/playwright
# in a test:
import {AxeBuilder} from '@axe-core/playwright';
const results = await new AxeBuilder({page}).analyze();

# pa11y CLI — quick smoke test
npx pa11y http://localhost:3000 --runner axe --standard WCAG2AA

# pa11y-ci with config
echo '{"defaults":{"runner":"axe","standard":"WCAG2AA"},"urls":["http://localhost:3000","http://localhost:3000/login"]}' > .pa11yci
npx pa11y-ci

# Lighthouse CI
npx -p @lhci/cli lhci autorun --collect.url=http://localhost:3000 \
  --assert.preset=lighthouse:no-pwa
```

## Component-level checklist (manual, fast)

For each interactive component, verify:

### Buttons / links / icon-buttons (A1)
- [ ] Has an accessible name: visible text, OR `aria-label`, OR `aria-labelledby`
- [ ] Icon-only button: `aria-label="Close"` (and the icon is `aria-hidden="true"`)
- [ ] `<a>` for navigation, `<button>` for actions — not interchangeable
- [ ] In-app navigation uses `<Link>` (or framework equivalent), not `<a href>`

### Click targets (A2)
- [ ] No `onClick` on `<div>`/`<span>` — use `<button>` (or add `role="button"`,
      `tabIndex={0}`, and `onKeyDown` handling Space/Enter — but really, use a button)
- [ ] Touch target ≥ 44×44 px (WCAG AAA, but a good baseline)

### Forms (A3)
- [ ] Every `<input>`/`<select>`/`<textarea>` has a `<label htmlFor>` OR
      `aria-label` OR `aria-labelledby`
- [ ] Required fields announced (`required` + `aria-required` if visual indicator
      isn't a `*` with announced meaning)
- [ ] Error messages linked via `aria-describedby` — not just colour
- [ ] `autocomplete` set to a [valid token][autocomplete] when applicable

[autocomplete]: https://developer.mozilla.org/docs/Web/HTML/Attributes/autocomplete

### Focus (A5, A8)
- [ ] Visible focus ring on every interactive element (don't `outline: none`
      without a `:focus-visible` replacement)
- [ ] Modal/dialog traps focus while open, returns focus on close
- [ ] No positive `tabIndex` (1, 2, 3...) — only `0` (focusable in source order)
      or `-1` (programmatic only)
- [ ] Skip-to-main link at the top of the page

### Colour & motion (A4)
- [ ] Information not conveyed by colour alone (status uses icon + text + colour)
- [ ] Contrast: text ≥ 4.5:1 (3:1 for large text), UI elements ≥ 3:1
- [ ] `prefers-reduced-motion` respected for animations

### Structure (A6)
- [ ] Exactly one `<h1>` per page
- [ ] No heading levels skipped (`<h1>` → `<h3>` is wrong)
- [ ] Landmarks: `<header>`, `<nav>`, `<main>`, `<footer>`
- [ ] Lists use `<ul>`/`<ol>`; tables use `<th scope>`

### Images (A7)
- [ ] Content image: `alt="<what it conveys, not what it is>"`
- [ ] Decorative image: `alt=""` (empty, not missing)
- [ ] Complex image (chart, diagram): `alt` summary + linked long description

### Links (A9)
- [ ] Link text makes sense out of context (no "click here", "read more"
      repeated 12 times — a screen reader rotor lists them all)
- [ ] External link: visually + announced (e.g. `aria-label="Docs (opens new tab)"`)

## Common React / Next.js a11y patterns

```tsx
// ✓ icon button
<button type="button" aria-label="Close" onClick={onClose}>
  <XIcon aria-hidden="true" />
</button>

// ✓ form field with error
<label htmlFor="email">Email</label>
<input
  id="email"
  type="email"
  required
  aria-required="true"
  aria-invalid={!!error}
  aria-describedby={error ? "email-error" : undefined}
/>
{error && <p id="email-error" role="alert">{error}</p>}

// ✓ in-app nav
import Link from "next/link";
<Link href="/dashboard">Dashboard</Link>  // not <a href>

// ✓ modal essentials (use Radix/Headless UI/React Aria for free)
// - role="dialog" aria-modal="true"
// - aria-labelledby pointing at the title
// - focus trap inside, focus restore on close
// - Esc closes
```

## When in doubt: use a primitive library

Radix UI, Headless UI, React Aria (Adobe), shadcn/ui all ship a11y-correct
primitives for combobox, dialog, tabs, popover, listbox. Reinventing these is
where most a11y bugs come from.