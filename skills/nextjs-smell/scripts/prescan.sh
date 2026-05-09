#!/usr/bin/env bash
# prescan.sh — frontend-smell pre-scan runner
# Runs available CLI tools against a TypeScript / Next.js project and prints a
# digest mapped to smell IDs. Skips any tool that isn't installed.
#
# Usage:  bash scripts/prescan.sh [project-root]
#         (defaults to current dir)
#
# Exit code is always 0 — this is a diagnostic, not a gate.

set -u
ROOT="${1:-.}"
cd "$ROOT" || { echo "no such dir: $ROOT" >&2; exit 1; }

C_RED=$'\e[31m'; C_YEL=$'\e[33m'; C_DIM=$'\e[2m'; C_BOLD=$'\e[1m'; C_RST=$'\e[0m'

hr()      { printf '%s\n' '────────────────────────────────────────────────────────────'; }
title()   { printf '\n%s%s%s\n' "$C_BOLD" "$1" "$C_RST"; hr; }
skipped() { printf '%s· skipped: %s%s\n' "$C_DIM" "$1" "$C_RST"; }
have()    { command -v "$1" >/dev/null 2>&1; }
nx()      { have npx && npx --no-install --yes "$@" 2>&1; }

# Detect package manager — affects how we run scripts
PM="npm"; [ -f pnpm-lock.yaml ] && PM="pnpm"
[ -f yarn.lock ] && PM="yarn"
[ -f bun.lockb ] && PM="bun"

printf '%sFrontend pre-scan%s  (root: %s, pm: %s)\n' "$C_BOLD" "$C_RST" "$PWD" "$PM"

# ── 1. tsc — type errors → T1, T2, T9 ────────────────────────────────────────
title "TypeScript (tsc --noEmit)"
if [ -f tsconfig.json ] && have npx; then
  out=$(npx --no-install tsc --noEmit --pretty false 2>&1 || true)
  count=$(printf '%s\n' "$out" | grep -cE '^[^ ].*\.tsx?\([0-9]+,[0-9]+\): error TS' || true)
  if [ "$count" -gt 0 ]; then
    printf '%s%d type errors%s — see T1/T2/T9\n' "$C_RED" "$count" "$C_RST"
    printf '%s\n' "$out" | grep -E '^[^ ].*error TS' | head -20
    [ "$count" -gt 20 ] && printf '%s… +%d more%s\n' "$C_DIM" "$((count-20))" "$C_RST"
  else
    echo "✓ no type errors"
  fi
else
  skipped "tsc (no tsconfig.json or no npx)"
fi

# ── 2. Linter — Biome > ESLint ───────────────────────────────────────────────
title "Linter (Biome / ESLint)"
if [ -f biome.json ] || [ -f biome.jsonc ]; then
  if have npx; then
    out=$(npx --no-install @biomejs/biome check --reporter=summary . 2>&1 || true)
    printf '%s\n' "$out" | tail -30
  else
    skipped "biome (no npx)"
  fi
elif [ -f eslint.config.js ] || [ -f eslint.config.mjs ] || [ -f eslint.config.ts ] || [ -f .eslintrc.json ] || [ -f .eslintrc.js ]; then
  if have npx; then
    out=$(npx --no-install eslint --max-warnings=0 --format=compact . 2>&1 || true)
    err=$(printf '%s\n' "$out" | grep -cE ': (Error|Warning) -' || true)
    printf '%s findings\n' "$err"
    printf '%s\n' "$out" | grep -E ': (Error|Warning) -' | head -20
  else
    skipped "eslint (no npx)"
  fi
else
  skipped "no biome.json or eslint config found"
fi

# ── 3. knip — dead code → B6, L3, D5 ─────────────────────────────────────────
title "Dead code (knip)"
if have npx; then
  out=$(npx --no-install knip --reporter compact 2>&1 || true)
  if printf '%s\n' "$out" | grep -qE '(not found|Could not|Cannot find)'; then
    skipped "knip (not installed — pnpm add -D knip)"
  else
    printf '%s\n' "$out" | tail -40
  fi
else
  skipped "knip (no npx)"
fi

# ── 4. Bundle hint — package.json deps that are known heavy ─────────────────
title "Bundle suspects (heavyweight deps in package.json)"
if [ -f package.json ]; then
  for pkg in lodash moment chart.js three @mui/material @mui/icons-material antd \
             react-icons recharts framer-motion @fullcalendar/core @ckeditor/ckeditor5-build-classic \
             draft-js quill @aws-sdk/client-s3 firebase; do
    if grep -qE "\"$pkg\"\\s*:" package.json; then
      printf '%s· %s%s — check if loaded on critical client routes (B1/B2)\n' "$C_YEL" "$pkg" "$C_RST"
    fi
  done
  echo "(run 'next build' + @next/bundle-analyzer for per-route truth)"
else
  skipped "no package.json"
fi

# ── 5. RSC boundary static check (bundled script) ───────────────────────────
title "RSC boundary check (static)"
if [ -f "$(dirname "$0")/rsc-boundary-check.mjs" ] && have node; then
  node "$(dirname "$0")/rsc-boundary-check.mjs" . || true
else
  skipped "rsc-boundary-check.mjs not available"
fi

# ── 6. Stylelint — CSS smells → S1, S2, D7 ──────────────────────────────────
title "Stylelint"
if [ -f .stylelintrc ] || [ -f .stylelintrc.json ] || [ -f stylelint.config.js ] || [ -f stylelint.config.mjs ]; then
  if have npx; then
    out=$(npx --no-install stylelint "**/*.{css,scss}" --formatter compact 2>&1 || true)
    printf '%s\n' "$out" | tail -30
  fi
else
  skipped "no stylelint config"
fi

# ── 7. madge — circular imports → B6 ────────────────────────────────────────
title "Circular imports (madge)"
if have npx; then
  out=$(npx --no-install madge --circular --extensions ts,tsx,js,jsx . 2>&1 || true)
  if printf '%s\n' "$out" | grep -qE '(not found|Could not|Cannot find)'; then
    skipped "madge (not installed — npm i -g madge or use depcheck)"
  else
    printf '%s\n' "$out" | head -20
  fi
fi

# ── 8. Bundle suspects (bundled script) ─────────────────────────────────────
title "Heavy imports in client files"
if [ -f "$(dirname "$0")/bundle-suspects.mjs" ] && have node; then
  node "$(dirname "$0")/bundle-suspects.mjs" . || true
else
  skipped "bundle-suspects.mjs not available"
fi

# ── 9. Next.js config sniff ─────────────────────────────────────────────────
title "Next.js config sniff"
for f in next.config.js next.config.mjs next.config.ts; do
  if [ -f "$f" ]; then
    grep -nE '(output|images|experimental|reactStrictMode|swcMinify)' "$f" | head -10
    grep -qE 'reactStrictMode\s*:\s*false' "$f" && \
      printf '%s⚠ reactStrictMode is OFF — masks effect bugs%s\n' "$C_YEL" "$C_RST"
    break
  fi
done

# ── 10. tsconfig strict-mode sniff ──────────────────────────────────────────
title "tsconfig strict flags"
if [ -f tsconfig.json ] && have node; then
  node -e '
    try {
      const t = JSON.parse(require("fs").readFileSync("tsconfig.json","utf8").replace(/\/\*[\s\S]*?\*\/|\/\/.*/g,""));
      const c = t.compilerOptions || {};
      const want = ["strict","noUncheckedIndexedAccess","exactOptionalPropertyTypes","noImplicitOverride","noFallthroughCasesInSwitch"];
      for (const k of want) console.log((c[k]?"✓":"✗")+" "+k+": "+(c[k]??"unset"));
    } catch(e) { console.log("(cannot parse tsconfig.json)"); }
  '
fi

hr
printf '%sDone.%s Map findings to smells in SKILL.md §Taxonomy. Lighthouse/axe/pa11y are runtime — run them against a deployed preview separately.\n' "$C_BOLD" "$C_RST"