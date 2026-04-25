# Variable Tracking — Phantom, Leaked, Shadowed

## Variable State Taxonomy

| State | Definition | Smell |
|---|---|---|
| **Live** | Defined in reachable scope, read at least once | — |
| **Phantom** | Defined but never read anywhere | M2 |
| **Leaked** | Scoped to domain A, visible/used in unrelated domain B | M7 |
| **Shadowed** | Re-defined before first read — original value discarded | M2 |
| **Latent** | Read but never defined in any reachable path | C1 (silent empty string) |
| **Thermometer** | One of 5+ vars controlling a single binary decision | H8 |

---

## How to Track Variables (manual, without tooling)

### Step 1: Build the definition list
For each variable: WHERE is it set?
- CI/CD UI secret
- `.env` file
- `export` in shell
- `variables:` block in CI YAML
- `os.getenv()` default value
- Hardcoded assignment

### Step 2: Build the usage list
WHERE is each variable read?
- Referenced in script steps
- Passed to functions / subprocesses
- Used in conditionals
- Interpolated into strings

### Step 3: Cross-reference
```
Variable         | Defined          | Used             | State
─────────────────|──────────────────|──────────────────|────────
IMAGE_TAG        | build job (output)| deploy job       | Live
MAX_RETRIES      | config.py:14     | (nowhere)        | Phantom
AWS_SECRET_KEY   | build job secret | test job script  | Leaked
DEPLOY_DRY_RUN   | 3 places         | (nowhere)        | Phantom+Shadowed
```

---

## Thermometer Pattern — Detection

Threshold: 5+ boolean/flag variables gating the same code path.

```bash
# RED FLAG — 6 variables for a binary deploy decision
if [[ "$DEPLOY_ENABLED" == "true" ]] &&
   [[ "$ENV_FLAG" != "skip" ]] &&
   [[ "$DEPLOY_MODE" != "dry" ]] &&
   [[ "$CI_PIPELINE_SOURCE" == "push" ]] &&
   [[ "$SKIP_DEPLOY" != "1" ]] &&
   [[ "$FORCE_NO_DEPLOY" != "true" ]]; then
```

**Fix pattern**: compute intent once at entrypoint.
```bash
SHOULD_DEPLOY=$(
  [[ "$DEPLOY_ENABLED" == "true" ]] &&
  [[ "$CI_PIPELINE_SOURCE" == "push" ]] &&
  [[ "$DEPLOY_MODE" != "dry" ]] &&
  echo "true" || echo "false"
)
# then use $SHOULD_DEPLOY everywhere
```

---

## Environment Leakage — Detection

Variables leak when:
1. A `variables:` block is defined at pipeline level (global) but only relevant to one job
2. Secrets for prod are visible in test/lint jobs (exposure risk)
3. Build-time config (compiler flags) bleeds into runtime jobs

```yaml
# BAD — PROD_DB_URL global, visible to lint and test jobs
variables:
  PROD_DB_URL: "postgres://..."

lint:
  script: flake8 .   # has no use for PROD_DB_URL, but can echo it

# GOOD — scope to deploy only
deploy:
  variables:
    PROD_DB_URL: "postgres://..."
  script: ./deploy.sh
```
