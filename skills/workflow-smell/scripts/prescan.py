#!/usr/bin/env python3
"""
prescan.py — Static grep-level pre-scan for workflow smell hints.
Runs before semantic analysis. Outputs JSON smell-hint map.

Usage:
    python scripts/prescan.py <file_or_dir> [--json] [--threshold LOW|MED|HIGH]

Output: JSON to stdout (or pretty-printed table if --json not set)
"""

import sys, os, re, json, argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

# ── Smell pattern registry ────────────────────────────────────────────────────

@dataclass
class Hit:
    smell_id: str
    severity: str          # CRITICAL | HIGH | MEDIUM | LOW
    confidence: str        # HIGH | MED | LOW
    file: str
    line: int
    match: str
    note: str

PATTERNS: list[dict] = [
    # ── CRITICAL ──
    dict(id="C1", sev="CRITICAL", conf="HIGH",
         regex=r"\|\|\s*true",
         note="Silent failure masking — errors swallowed"),
    dict(id="C1", sev="CRITICAL", conf="HIGH",
         regex=r"2\s*>\s*/dev/null",
         note="Stderr suppressed — may hide real errors"),
    dict(id="C1", sev="CRITICAL", conf="MED",
         regex=r"exit\s+0\b",
         note="Unconditional exit 0 — may mask failure"),
    dict(id="C3", sev="CRITICAL", conf="MED",
         regex=r">>\s*\w+",
         note="Append-mode write — check idempotency"),

    # ── HIGH ──
    dict(id="H3", sev="HIGH", conf="HIGH",
         regex=r"parallel:\s*([1-9][0-9]+)",
         note="High parallelism — verify runner core count"),
    dict(id="H4", sev="HIGH", conf="MED",
         regex=r"if\s+\[\s+[\"']?(true|false|1|0)[\"']?\s+[\"']?(true|false|1|0)[\"']?\s+\]",
         note="Static condition in if-block — always same branch"),
    dict(id="H6", sev="HIGH", conf="MED",
         regex=r"stage:\s+\w+",
         note="Stage declared — verify needs: graph covers ordering"),
    dict(id="H8", sev="HIGH", conf="LOW",
         regex=r"\$\{?\w*(FLAG|TOGGLE|ENABLED|DISABLED|MODE|SWITCH)\w*\}?",
         note="Feature-flag variable — check for thermometer pattern"),

    # ── MEDIUM ──
    dict(id="M2", sev="MEDIUM", conf="LOW",
         regex=r"^\s*export\s+\w+\s*=",
         note="Exported variable — check if actually consumed downstream"),
    dict(id="M4", sev="MEDIUM", conf="MED",
         regex=r"retry:\s*[2-9]",
         note="Retry configured — verify it's for flakiness, not logic errors"),
    dict(id="M5", sev="MEDIUM", conf="MED",
         regex=r"#.*(build|deploy|push|test|install).*\n.*\b(push|deploy|build|test|install)\b",
         note="Comment/code action mismatch candidate"),
    dict(id="M8", sev="MEDIUM", conf="MED",
         regex=r"==\s*[\d]+\.[\d]+\.[\d]+",
         note="Pinned version — check age and update automation"),
    dict(id="M9", sev="MEDIUM", conf="MED",
         regex=r"(docker\.io|registry-1\.docker\.io|ghcr\.io|public\.ecr\.aws|quay\.io)",
         note="External registry reference — check mirror/fallback strategy"),
    dict(id="C4", sev="CRITICAL", conf="MED",
         regex=r"(docker\s+login|aws\s+ecr\s+get-login|gcloud\s+auth)",
         note="Auth command — check if token can be passed instead of re-acquired"),

    # ── LOW ──
    dict(id="L1", sev="LOW", conf="HIGH",
         regex=r"^\s*(?:RUN\s+)?echo\s+[\"']",
         note="Debug echo — check if intentional or debug leftover"),
    dict(id="L4", sev="LOW", conf="HIGH",
         regex=r"#\s*TODO",
         note="TODO comment — check if stage/function is stub"),
    dict(id="L5", sev="LOW", conf="HIGH",
         regex=r"^\s*#\s+\w.{20,}",
         note="Large commented block — check if configuration archaeology"),
    dict(id="L7", sev="LOW", conf="MED",
         regex=r'(?<!["\w])\b([3-9]\d{2,}|[1-9]\d{3,})\b(?!["\w])',
         note="Magic number — consider named constant or env var"),

    # ── Secrets ──
    dict(id="C4", sev="CRITICAL", conf="HIGH",
         regex=r"(AKIA[0-9A-Z]{16}|sk-[a-zA-Z0-9]{20,}|['\"]?[A-Z_]*(?:SECRET|TOKEN|API_KEY)[A-Z_]*['\"]?\s*=\s*['\"][^'\"${\s]{8,}['\"])",
         note="Possible hardcoded credential"),
]

# ── File type filters ─────────────────────────────────────────────────────────

INCLUDE_EXTENSIONS = {
    ".yml", ".yaml", ".sh", ".bash", ".zsh",
    ".py", ".toml", ".cfg", ".ini", ".env",
    ".dockerfile", ".mk", "", "Makefile", "Dockerfile",
}

def should_scan(path: Path) -> bool:
    name = path.name
    if name in {"Makefile", "Dockerfile", "Jenkinsfile"}:
        return True
    return path.suffix.lower() in INCLUDE_EXTENSIONS

# ── Scanner ───────────────────────────────────────────────────────────────────

def scan_file(path: Path) -> list[Hit]:
    hits = []
    try:
        text = path.read_text(errors="replace")
    except (PermissionError, IsADirectoryError):
        return hits

    lines = text.splitlines()
    for pat in PATTERNS:
        rx = re.compile(pat["regex"], re.IGNORECASE | re.MULTILINE)
        for m in rx.finditer(text):
            lineno = text[: m.start()].count("\n") + 1
            snippet = lines[lineno - 1].strip()[:120]
            hits.append(Hit(
                smell_id=pat["id"],
                severity=pat["sev"],
                confidence=pat["conf"],
                file=str(path),
                line=lineno,
                match=snippet,
                note=pat["note"],
            ))
    return hits

def scan(target: Path) -> list[Hit]:
    if target.is_file():
        return scan_file(target) if should_scan(target) else []
    hits = []
    for p in target.rglob("*"):
        if p.is_file() and should_scan(p):
            # skip .git, node_modules, __pycache__, venv
            parts = set(p.parts)
            if parts & {".git", "node_modules", "__pycache__", ".venv", "venv", ".tox"}:
                continue
            hits.extend(scan_file(p))
    return hits

# ── Aggregation ───────────────────────────────────────────────────────────────

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
SEVERITY_WEIGHT = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}

def aggregate(hits: list[Hit]) -> dict:
    by_smell: dict[str, list[Hit]] = {}
    for h in hits:
        by_smell.setdefault(h.smell_id, []).append(h)

    smells_summary = []
    score = 0
    for sid, group in sorted(by_smell.items(), key=lambda x: SEVERITY_ORDER.get(x[1][0].severity, 9)):
        sev = group[0].severity
        score += SEVERITY_WEIGHT[sev] * min(len(group), 3)  # cap contribution per smell
        smells_summary.append({
            "smell_id": sid,
            "severity": sev,
            "confidence": group[0].confidence,
            "count": len(group),
            "locations": [{"file": h.file, "line": h.line, "match": h.match} for h in group[:5]],
            "note": group[0].note,
        })

    score = min(score, 20)
    verdict = (
        "✅ Lean" if score <= 3 else
        "🟡 Needs Trim" if score <= 7 else
        "🟠 Complexity Trap" if score <= 13 else
        "🔴 Rip It Down"
    )

    # Cluster detection (simple heuristic from IDs found)
    found_ids = set(by_smell.keys())
    clusters = []
    CLUSTER_RULES = [
        ({"C1","M4","H4"}, "Confidence Theater", "CRITICAL"),
        ({"H1","H2","M1"}, "Rube Goldberg Machine", "HIGH"),
        ({"H3","C5","M3"}, "Cargo-Cult Performance", "HIGH"),
        ({"H5","H7","L4"}, "Future-Proof Graveyard", "MEDIUM"),
        ({"H8","M2","M7"}, "Variable Entropy", "MEDIUM"),
        ({"M6","M9","C4"}, "Docker Debt", "MEDIUM"),
    ]
    for ids, name, sev in CLUSTER_RULES:
        if ids & found_ids == ids:
            clusters.append({"name": name, "severity": sev, "smells": list(ids)})
            score = min(score + 2, 20)

    return {
        "score": score,
        "verdict": verdict,
        "total_hits": len(hits),
        "smells": smells_summary,
        "clusters": clusters,
        "files_scanned": len({h.file for h in hits}),
    }

# ── Pretty printer ────────────────────────────────────────────────────────────

SEV_COLOR = {
    "CRITICAL": "\033[91m",
    "HIGH":     "\033[31m",
    "MEDIUM":   "\033[33m",
    "LOW":      "\033[32m",
}
RESET = "\033[0m"

def pretty_print(result: dict):
    print(f"\n{'═'*60}")
    print(f"  Workflow Pre-Scan")
    print(f"  Score: {result['score']}/20  {result['verdict']}")
    print(f"  Files scanned: {result['files_scanned']}  Total hits: {result['total_hits']}")
    print(f"{'═'*60}\n")

    for s in result["smells"]:
        col = SEV_COLOR.get(s["severity"], "")
        print(f"{col}[{s['smell_id']}] {s['severity']} · {s['note']}{RESET}")
        print(f"    Confidence: {s['confidence']}  Occurrences: {s['count']}")
        for loc in s["locations"][:3]:
            print(f"    → {loc['file']}:{loc['line']}")
            print(f"      {loc['match'][:80]}")
        print()

    if result["clusters"]:
        print(f"{'─'*60}")
        print("COMPOUND CLUSTERS DETECTED:")
        for c in result["clusters"]:
            col = SEV_COLOR.get(c["severity"], "")
            print(f"{col}  ⚠ {c['name']} ({', '.join(c['smells'])}){RESET}")
        print()

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Workflow smell pre-scanner")
    p.add_argument("target", help="File or directory to scan")
    p.add_argument("--json", action="store_true", help="Output JSON instead of table")
    p.add_argument("--threshold", default="LOW",
                   choices=["LOW","MED","HIGH"], help="Min confidence to report")
    args = p.parse_args()

    path = Path(args.target)
    if not path.exists():
        print(f"Error: {path} not found", file=sys.stderr)
        sys.exit(1)

    hits = scan(path)

    conf_order = {"HIGH": 0, "MED": 1, "LOW": 2}
    threshold = conf_order[args.threshold]
    hits = [h for h in hits if conf_order.get(h.confidence, 2) <= threshold]

    result = aggregate(hits)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        pretty_print(result)

if __name__ == "__main__":
    main()
