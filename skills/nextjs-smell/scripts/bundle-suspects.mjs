#!/usr/bin/env node
/**
 * bundle-suspects.mjs
 *
 * Scans client-side files (those reachable from `"use client"` files) for known
 * heavy-import smells (B1, B2). Catches what `next build` would also catch, but
 * faster and without needing a full build.
 *
 * Reports:
 *   - whole-library imports that defeat tree-shaking (B1)
 *   - heavy libs imported eagerly into client bundles (B2)
 *
 * Usage:  node scripts/bundle-suspects.mjs [project-root]
 */
import {readFileSync, readdirSync, statSync} from 'node:fs';
import {join, extname, relative, resolve} from 'node:path';

const root = resolve(process.argv[2] || '.');
const exts = new Set(['.ts', '.tsx', '.js', '.jsx', '.mjs']);
const skip = new Set(['node_modules', '.next', '.turbo', 'dist', 'build', 'out', '.git']);

// Patterns: [regex, smell-id, advice]
const PATTERNS = [
  [/^import\s+_\s+from\s+['"]lodash['"]/m, 'B1',
    "lodash whole-import — use 'lodash-es' + named imports, or per-method (lodash/debounce)"],
  [/from\s+['"]moment['"]/m, 'B2',
    "moment is ~70KB gzip + locale. Use date-fns, dayjs, or Intl.DateTimeFormat"],
  [/^import\s+\*\s+as\s+\w+\s+from\s+['"]lucide-react['"]/m, 'B1',
    "lucide-react namespace import — use named imports: { Search, Menu }"],
  [/from\s+['"]@mui\/material['"]/m, 'B1',
    "@mui/material root import — use deep imports: '@mui/material/Button'"],
  [/from\s+['"]@mui\/icons-material['"]/m, 'B1',
    "@mui/icons-material root — use '@mui/icons-material/SpecificIcon'"],
  [/from\s+['"]chart\.js['"]/m, 'B2',
    "chart.js is heavy — load via next/dynamic({ ssr: false }) and tree-shake"],
  [/from\s+['"]three['"]/m, 'B2',
    "three.js is huge — next/dynamic + Suspense, never eager-import"],
  [/from\s+['"]@aws-sdk\/client-/m, 'B2',
    "aws-sdk client in browser bundle — should be server-side only"],
  [/from\s+['"]firebase\/(?!app|auth)/m, 'B2',
    "firebase modules — verify only what's needed is imported, lazy-load if possible"],
  [/^import\s+\*\s+as\s+\w+\s+from\s+['"]@radix-ui\//m, 'B1',
    "Radix namespace import — use named imports"],
  [/from\s+['"]ckeditor/m, 'B2',
    "CKEditor build is 1MB+ — must be next/dynamic, no SSR"],
  [/from\s+['"]quill['"]/m, 'B2',
    "Quill is large — next/dynamic, no SSR"],
];

// Find client files first
const clientFiles = new Set();
function walk(d, into) {
  let entries; try { entries = readdirSync(d); } catch { return; }
  for (const e of entries) {
    if (skip.has(e)) continue;
    const p = join(d, e);
    const s = statSync(p);
    if (s.isDirectory()) walk(p, into);
    else if (exts.has(extname(p))) into.push(p);
  }
}
const allFiles = [];
walk(root, allFiles);

for (const f of allFiles) {
  let src; try { src = readFileSync(f, 'utf8'); } catch { continue; }
  if (/^\s*(["']use client["'])\s*;?/m.test(src.slice(0, 200))) {
    clientFiles.add(f);
  }
}

// Also include files in `pages/` (legacy router) — all client by default
for (const f of allFiles) {
  if (/[\\/]pages[\\/](?!api[\\/])/.test(f)) clientFiles.add(f);
}

// Scan
const hits = [];
for (const f of clientFiles) {
  let src; try { src = readFileSync(f, 'utf8'); } catch { continue; }
  for (const [re, id, advice] of PATTERNS) {
    if (re.test(src)) hits.push({file: relative(root, f), id, advice});
  }
}

const C_YEL = '\x1b[33m', C_DIM = '\x1b[2m', C_RST = '\x1b[0m';
if (!hits.length) {
  console.log('✓ no known heavy-import patterns in client files');
} else {
  // Group by advice so the same smell across many files reads cleanly
  const byAdvice = new Map();
  for (const h of hits) {
    if (!byAdvice.has(h.advice)) byAdvice.set(h.advice, {id: h.id, files: []});
    byAdvice.get(h.advice).files.push(h.file);
  }
  for (const [advice, {id, files}] of byAdvice) {
    console.log(`${C_YEL}${id}${C_RST}  ${advice}`);
    for (const f of files.slice(0, 8)) console.log(`  ${f}`);
    if (files.length > 8) console.log(`  ${C_DIM}… +${files.length - 8} more${C_RST}`);
  }
}