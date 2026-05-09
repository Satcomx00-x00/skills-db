# CLI Cheatsheet

Every tool the pre-scan touches, with one-liners and what to do with the output.

## Type checking

```bash
# Once
npx tsc --noEmit

# Watch
npx tsc --noEmit --watch

# Project references
npx tsc -b --noEmit
```
**Output → smells:** errors → T1, T2, T9. "Cannot find module" often → B6 (barrel)
or D5 (drift).

## Biome — linter + formatter (Rust, fast)

```bash
# Init (greenfield)
npx @biomejs/biome init

# Check (lint + format diff, no writes)
npx @biomejs/biome check .

# Apply safe fixes
npx @biomejs/biome check --write .

# Apply all fixes including unsafe
npx @biomejs/biome check --write --unsafe .

# CI-friendly summary
npx @biomejs/biome check --reporter=summary .
```
**Output → smells:** correctness rules → R1, R2; a11y group → A1–A4, A7;
suspicious group → T1, T7. Biome v2 has type-aware rules without a TS pass.

## ESLint v9 (flat config)

```bash
npx eslint .
npx eslint . --max-warnings=0 --format compact
npx eslint . --fix
```
Recommended plugins for Next.js + TS frontends:
- `@typescript-eslint/eslint-plugin` (now bundled in `typescript-eslint`)
- `eslint-plugin-react`, `eslint-plugin-react-hooks`
- `eslint-plugin-jsx-a11y`
- `@next/eslint-plugin-next` (or just `eslint-config-next`)
- `eslint-plugin-import` (for B6 barrel/circular)
- `eslint-plugin-unused-imports`

**Output → smells:** `react-hooks/exhaustive-deps` → R1; `jsx-a11y/*` → A1–A9;
`@next/next/*` → N9, N10, N14.

## Knip — dead code, unused exports, unused deps

```bash
# First-time: generates knip.json from heuristics
npx knip

# JSON report for tooling
npx knip --reporter json > knip-report.json

# Production-only (ignores dev deps)
npx knip --production

# Auto-fix: remove unused exports / deps
npx knip --fix
```
**Output → smells:** unused files → L3; unused exports → B6; unused deps → B6;
unlisted deps → may indicate accidental Node usage in client (N2).

## Stylelint — CSS smells

```bash
npx stylelint "**/*.css" "**/*.scss"
npx stylelint "**/*.css" --fix
```
Useful configs: `stylelint-config-standard`, `stylelint-config-tailwindcss`.

**Output → smells:** `declaration-no-important` → S1; `no-descending-specificity`
→ S1; `media-feature-name-value-no-unknown` → D7.

## Knip + Madge — circulars and graph

```bash
npx madge --circular --extensions ts,tsx,js,jsx src/
# Visualise:
npx madge --image graph.svg src/
```
**Output → smells:** B6 (barrel/circular).

## next build + bundle analyzer

```bash
# Add to next.config.js:
#   import bundleAnalyzer from "@next/bundle-analyzer";
#   export default bundleAnalyzer({enabled: process.env.ANALYZE === "true"})({...});

ANALYZE=true npx next build
# Opens HTML reports for client/edge/server bundles.
```
**Output → smells:** outsized chunks → B1, B2, B6; vendor splits → B6.

```bash
# Lightweight alternative — just per-route page sizes
npx next build  # the build summary table at the end
```

## Lighthouse / Lighthouse CI

```bash
# One-off CLI
npx lighthouse http://localhost:3000 --view --preset=desktop

# CI (with assertions)
npx -p @lhci/cli lhci autorun \
  --collect.url=http://localhost:3000 \
  --assert.preset=lighthouse:no-pwa \
  --upload.target=temporary-public-storage
```
Sample `.lighthouserc.json`:
```json
{
  "ci": {
    "collect": {"url": ["http://localhost:3000"], "numberOfRuns": 3},
    "assert": {"assertions": {
      "categories:performance": ["error", {"minScore": 0.9}],
      "categories:accessibility": ["error", {"minScore": 0.95}],
      "categories:best-practices": ["warn", {"minScore": 0.9}]
    }}
  }
}
```
**Output → smells:** LCP slow → P3, P4, B2; CLS → B4; unused JS → B1, B2;
a11y score → A1–A9.

## axe / pa11y — runtime a11y

```bash
# Pa11y one-off
npx pa11y http://localhost:3000 --runner axe --standard WCAG2AA

# Pa11y CI with config
cat > .pa11yci.json <<'EOF'
{ "defaults": {"runner": "axe", "standard": "WCAG2AA", "timeout": 30000},
  "urls": ["http://localhost:3000", "http://localhost:3000/login"] }
EOF
npx pa11y-ci

# axe-core + Playwright (programmatic, integrates with tests)
npm i -D @axe-core/playwright
```
**Output → smells:** A1–A9 with rule IDs you can map back to the taxonomy.

## depcheck (fallback if knip not used)

```bash
npx depcheck
```

## Putting it together — minimal CI a11y/perf gate

```yaml
# .github/workflows/quality.yml
name: quality
on: [pull_request]
jobs:
  static:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: pnpm }
      - run: pnpm install --frozen-lockfile
      - run: pnpm tsc --noEmit
      - run: pnpm biome check .   # or: pnpm eslint .
      - run: pnpm knip --production
  runtime:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: pnpm }
      - run: pnpm install --frozen-lockfile
      - run: pnpm build
      - run: pnpm start &  # serve
      - run: npx wait-on http://localhost:3000
      - run: npx pa11y-ci
      - run: npx -p @lhci/cli lhci autorun
```