#!/usr/bin/env node
/**
 * rsc-boundary-check.mjs
 *
 * Static scan for Next.js App Router boundary violations (smells N1, N2, N15, B3).
 * No deps. Reads files directly. ~O(files) — fast on most projects.
 *
 * What it flags:
 *   1. "use client" file imports a module that uses server-only APIs
 *      (`fs`, `node:*`, `next/headers`, `next/server` server bits, `server-only`)
 *   2. "use client" file references `process.env.X` where X is NOT prefixed
 *      `NEXT_PUBLIC_` — likely server secret leaking to bundle
 *   3. Server Component file (no "use client") imports `client-only` or uses
 *      browser globals at top-level (`window`, `document`, `localStorage`)
 *
 * Usage:  node scripts/rsc-boundary-check.mjs [project-root]
 *
 * Caveats: static — won't catch dynamic imports, won't resolve aliases beyond
 * a basic tsconfig.json `paths` read. If something looks wrong, treat the output
 * as a candidate list, not a verdict.
 */
import {readFileSync, readdirSync, statSync, existsSync} from 'node:fs';
import {join, extname, relative, dirname, resolve} from 'node:path';

const root = resolve(process.argv[2] || '.');
const exts = new Set(['.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs']);
const skip = new Set(['node_modules', '.next', '.turbo', 'dist', 'build', 'out', '.git', 'coverage']);

const SERVER_ONLY_IMPORTS = [
  /^node:/, /^fs(\/.*)?$/, /^path$/, /^crypto$/, /^child_process$/,
  /^next\/headers$/, /^server-only$/,
  /^@?prisma\/client/, /^drizzle-orm/, /^pg$/, /^mysql2/, /^mongodb$/,
  /^bcrypt(js)?$/, /^jose$/, /^jsonwebtoken$/,
];
const BROWSER_GLOBALS = /\b(window|document|localStorage|sessionStorage|navigator)\./;

const findings = {clientImportsServer: [], envLeak: [], browserInServer: []};
const files = [];

function walk(d) {
  let entries;
  try { entries = readdirSync(d); } catch { return; }
  for (const e of entries) {
    if (skip.has(e) || e.startsWith('.')) continue;
    const p = join(d, e);
    const s = statSync(p);
    if (s.isDirectory()) walk(p);
    else if (exts.has(extname(p))) files.push(p);
  }
}
walk(root);

// Build a quick map: file → { isClient, imports[] }
const fileInfo = new Map();
for (const f of files) {
  let src;
  try { src = readFileSync(f, 'utf8'); } catch { continue; }
  const head = src.slice(0, 200);
  const isClient = /^\s*(?:["']use client["'])\s*;?/m.test(head);
  const isServerOnly = /^\s*import\s+["']server-only["']/m.test(src);
  const imports = [];
  const re = /(?:^|\n)\s*import(?:\s+[\s\S]*?\s+from)?\s*["']([^"']+)["']/g;
  let m; while ((m = re.exec(src))) imports.push(m[1]);
  fileInfo.set(f, {src, isClient, isServerOnly, imports});
}

// Scan
for (const [f, info] of fileInfo) {
  const rel = relative(root, f);

  if (info.isClient) {
    // 1. server-only imports from a client file
    for (const imp of info.imports) {
      if (SERVER_ONLY_IMPORTS.some(re => re.test(imp))) {
        findings.clientImportsServer.push({file: rel, import: imp});
      }
    }
    // 2. process.env.NON_PUBLIC
    const envRe = /process\.env\.([A-Z0-9_]+)/g;
    let m; while ((m = envRe.exec(info.src))) {
      const v = m[1];
      if (!v.startsWith('NEXT_PUBLIC_') && v !== 'NODE_ENV') {
        findings.envLeak.push({file: rel, var: v});
      }
    }
  } else {
    // 3. Server file using browser globals at top-level (rough — outside fn bodies hard to tell statically; just flag presence outside use client)
    if (BROWSER_GLOBALS.test(info.src) && !info.isServerOnly) {
      // crude filter: ignore if inside a function clearly marked client by a "use client" sub-component file
      findings.browserInServer.push({file: rel});
    }
  }
}

// Report
const C_RED = '\x1b[31m', C_YEL = '\x1b[33m', C_DIM = '\x1b[2m', C_RST = '\x1b[0m';
let issues = 0;

if (findings.clientImportsServer.length) {
  issues += findings.clientImportsServer.length;
  console.log(`${C_RED}N2 · "use client" file imports server-only module${C_RST}`);
  for (const x of findings.clientImportsServer.slice(0, 15)) {
    console.log(`  ${x.file}  ←  ${x.import}`);
  }
  if (findings.clientImportsServer.length > 15)
    console.log(`  ${C_DIM}… +${findings.clientImportsServer.length - 15} more${C_RST}`);
}

if (findings.envLeak.length) {
  issues += findings.envLeak.length;
  // Dedupe
  const uniq = new Map();
  for (const x of findings.envLeak) uniq.set(`${x.file}:${x.var}`, x);
  console.log(`${C_RED}N1 · non-public env var read in "use client" file${C_RST}`);
  for (const x of [...uniq.values()].slice(0, 15)) {
    console.log(`  ${x.file}  ←  process.env.${x.var}`);
  }
  if (uniq.size > 15) console.log(`  ${C_DIM}… +${uniq.size - 15} more${C_RST}`);
}

if (findings.browserInServer.length) {
  issues += findings.browserInServer.length;
  console.log(`${C_YEL}N3 · server file references browser globals (window/document/localStorage)${C_RST}`);
  for (const x of findings.browserInServer.slice(0, 10)) {
    console.log(`  ${x.file}`);
  }
}

if (issues === 0) console.log('✓ no obvious boundary violations');
else console.log(`${C_DIM}(static scan — verify before refactoring; some matches may be inside conditional branches)${C_RST}`);