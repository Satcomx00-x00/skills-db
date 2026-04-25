# Antipatterns Reference — Per Ecosystem

## GitLab CI

### C1 · Silent Failure Masking
```yaml
# BAD
script:
  - kubectl apply -f manifests/ || true   # deploy failure = invisible

# GOOD
script:
  - kubectl apply -f manifests/
  - kubectl rollout status deployment/app --timeout=120s
```

### C2 · Ouroboros Pipeline
```yaml
# BAD — child pipeline includes same template as parent
trigger-child:
  trigger:
    include: .gitlab-ci.yml   # triggers itself
```
Fix: extract shared logic into a standalone template file, not the main CI file.

### C5 · Phantom Parallelism
```yaml
# BAD — all parallel jobs write to same shared volume
test:
  parallel: 8
  script:
    - pytest >> /shared/results.log   # serial due to file lock
```
Fix: write per-job artifacts, merge in a separate collect job.

### H1 · Wrapper Theater
```yaml
# BAD
trigger-build:
  stage: trigger
  script:
    - gitlab-runner exec docker build   # just proxies to next stage

# GOOD — just use needs: directly
build:
  stage: build
  needs: []
```

### H3 · Cargo-Cult Config
```yaml
# BAD — copied from StackOverflow, runner has 2 cores
variables:
  MAKEFLAGS: "-j32"
  GRADLE_OPTS: "-Xmx16g"   # runner has 4GB RAM
```

### H4 · Dead Rules Branch
```yaml
# BAD — second rule is unreachable (first matches all main commits)
rules:
  - if: '$CI_COMMIT_BRANCH == "main"'
    when: always
  - if: '$CI_COMMIT_BRANCH == "main"'
    when: manual   # never reached
```

### H6 · Temporal Coupling Without Declaration
```yaml
# BAD — test implicitly needs build output, but no needs: declared
build:
  stage: build
  artifacts: { paths: [dist/] }

test:
  stage: test
  # assumes build already ran — fragile if stages reorder
  script: pytest dist/
```
Fix: add `needs: [build]` to test job.

### M3 · Cache Miss Architecture
```yaml
# BAD — SHA in key = never hits
cache:
  key: "$CI_COMMIT_SHA-pip"
  paths: [.pip/]

# GOOD — key on lockfile hash
cache:
  key:
    files: [requirements.txt]
  paths: [.pip/]
```

### M4 · Retry Loop Around Logic Error
```yaml
# BAD — deploy fails because IMAGE_TAG is wrong, not flaky
deploy:
  retry: 3
  script:
    - helm upgrade app chart/ --set image.tag=$IMAGE_TAG
```

---

## Dockerfile

### M6 · Multi-Stage Mirage
```dockerfile
# BAD — same base, same files, no size reduction
FROM python:3.12 AS builder
WORKDIR /app
COPY . .
RUN pip install .

FROM python:3.12
COPY --from=builder /app /app  # copies everything, final image same size

# GOOD — use slim, copy only site-packages
FROM python:3.12 AS builder
RUN pip install --prefix=/install -r requirements.txt

FROM python:3.12-slim
COPY --from=builder /install /usr/local
COPY src/ /app/src/
```

### C4 · Credential Churn per Stage
```dockerfile
# BAD — re-auths inside build, leaks token into layer
RUN aws ecr get-login-password --region us-east-1 | docker login ...
RUN docker pull $BASE_IMAGE

# GOOD — use --secret mount (BuildKit)
RUN --mount=type=secret,id=aws,target=/root/.aws/credentials \
    aws ecr get-login-password | docker login ...
```

### C3 · Accidental Idempotency Break
```dockerfile
# BAD — re-running appends duplicates to sources.list
RUN echo "deb http://example.com/repo stable main" >> /etc/apt/sources.list
RUN apt-get update

# GOOD — idempotent write
RUN echo "deb http://example.com/repo stable main" > /etc/apt/sources.list.d/custom.list \
    && apt-get update
```

---

## Shell / Bash

### C1 · No Error Propagation
```bash
# BAD — errors in pipeline silently ignored
deploy.sh:
  build_image
  push_image
  update_manifest || true   # if this fails, deploy proceeds with old manifest

# GOOD
set -euo pipefail
build_image
push_image
update_manifest
```

### H8 · Thermometer Pattern
```bash
# BAD — 6 vars to decide: deploy or not
if [[ "$DEPLOY_ENABLED" == "true" ]] && \
   [[ "$ENV_FLAG" != "skip" ]] && \
   [[ "$DEPLOY_MODE" != "dry" ]] && \
   [[ "$CI_PIPELINE_SOURCE" == "push" ]] && \
   [[ "$SKIP_DEPLOY" != "1" ]] && \
   [[ "$FORCE_NO_DEPLOY" != "true" ]]; then
  deploy
fi

# GOOD — single SHOULD_DEPLOY computed once at entrypoint
```

### L3 · Alias Maze
```bash
# In .bashrc:
alias run='execute_task'
execute_task() { ./scripts/runner.sh "$@"; }
# In runner.sh:
exec ./scripts/run_task.sh "$@"
# In run_task.sh:
alias run='docker run --rm task-image'
```

---

## Python Project

### H5 · Abstract Nothingness
```python
# BAD — ABC with one implementor, no variation
class BaseExporter(ABC):
    @abstractmethod
    def export(self, data: list) -> bytes: ...

class CSVExporter(BaseExporter):
    def export(self, data: list) -> bytes:
        return "\n".join(",".join(row) for row in data).encode()

# CSVExporter is only ever instantiated directly. No other exporter exists.
# Fix: just use a function.
def export_csv(data: list) -> bytes:
    return "\n".join(",".join(row) for row in data).encode()
```

### M8 · Version Pin Drift
```
# requirements.txt — last updated 11 months ago
requests==2.28.1       # current: 2.32.3
boto3==1.26.0          # current: 1.34.84 (BREAKING changes in between)
cryptography==38.0.4   # CVE fixed in 41.x
```
Fix: add `pip-compile --upgrade` to CI, or configure Renovate/Dependabot.

### M2 · Phantom Variable
```python
# set in config.py
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# grep -r MAX_RETRIES . → only found in config.py
# Never read anywhere else
```

### H7 · Speculative Infrastructure
```python
# plugin_registry.py — 400 lines of plugin loader
# grep -r PluginRegistry . → only instantiated in tests
# No feature uses plugins yet; "planned for Q3 2022"
```
