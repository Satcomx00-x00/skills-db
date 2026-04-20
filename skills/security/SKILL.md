---
name: security
description: Application security practices — OWASP Top 10 mitigations, secret management, dependency scanning, and secure coding patterns for web and API projects. Use this skill whenever someone asks about securing an application, reviewing code for vulnerabilities, handling authentication or authorisation, managing secrets, scanning for dependency issues, or says things like "is this secure", "how do I prevent SQL injection", or "how should I store passwords" — even if they don't say "security".
license: MIT
metadata:
  author: Satcomx00-x00
  version: 2.0.0
---

# security

Application security practices — OWASP Top 10 mitigations, secret management, dependency scanning, and secure coding patterns for web and API projects.

## Workflow

When reviewing or implementing security:

1. **Model the threats first** — identify trust boundaries (API inputs, auth tokens, third-party data, env vars) before choosing controls
2. **Input validation and output escaping** — validate all input at entry points with an allowlist; escape output context-appropriately (HTML, SQL, shell, URL)
3. **Authentication and authorisation** — enforce authZ on every server-side endpoint (deny-by-default); validate tokens on every request; never trust client-supplied IDs
4. **Secrets out of code** — no hardcoded credentials; use a secrets manager or env vars; run `gitleaks` / `trufflehog` in CI and pre-commit
5. **Dependency and image scanning** — run `npm audit` / `pip-audit` / `trivy` in CI on every build; automate updates with Dependabot or Renovate

### OWASP Top 10 Quick Reference

| Risk | Key Control |
|------|------------|
| A01 Broken Access Control | Deny-by-default; validate resource ownership per request |
| A02 Cryptographic Failures | bcrypt/argon2id for passwords; TLS 1.2+; HSTS; encrypt PII at rest |
| A03 Injection | Parameterised queries; Zod/Pydantic validation; escape all output |
| A05 Security Misconfiguration | Security headers (Helmet); remove defaults; never commit `.env` |
| A06 Vulnerable Components | `npm audit` / `trivy` in CI; Dependabot auto-updates |
| A07 Auth Failures | MFA for admins; rate-limit login; `HttpOnly; Secure; SameSite` cookies |
| A09 Logging Failures | Log auth events; never log passwords/PII; alert on anomalies |

## Instructions

Apply these security practices when writing, reviewing, or auditing code:

### OWASP Top 10 Mitigations

**A01 – Broken Access Control**
- Enforce authorisation on every server-side route/endpoint, not just the UI
- Use deny-by-default: explicitly grant permissions, never assume
- Validate that the requesting user owns the resource they're accessing

**A02 – Cryptographic Failures**
- Never roll your own crypto — use established libraries (`bcrypt`, `argon2`, `libsodium`)
- Minimum password hashing: bcrypt with cost ≥ 12 or argon2id
- TLS 1.2+ for all connections; enforce HSTS
- Encrypt sensitive data at rest (PII, payment data, health records)

**A03 – Injection**
- Use parameterised queries / prepared statements — never string-concatenate SQL
- Validate and sanitise all user input at the boundary
- Use an allowlist for input validation, not a denylist
- Escape output context-appropriately (HTML, JSON, shell, URL)

**A05 – Security Misconfiguration**
- Remove default credentials and unused features/endpoints
- Set security headers: `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`
- Disable directory listing and server version disclosure
- Use environment-specific configs; never commit `.env` files

**A06 – Vulnerable and Outdated Components**
- Run `npm audit` / `pip-audit` / `trivy fs .` regularly
- Enable Dependabot or Renovate for automated dependency updates
- Pin dependency versions in lockfiles

**A07 – Identification and Authentication Failures**
- Enforce MFA for admin accounts
- Use secure session tokens (≥ 128 bits of entropy); regenerate after login
- Implement rate limiting and account lockout on login endpoints
- Use `HttpOnly`, `Secure`, `SameSite=Strict` on session cookies

**A09 – Security Logging and Monitoring Failures**
- Log authentication events (success, failure, lockout)
- Log access control failures
- Never log passwords, tokens, or PII
- Alert on anomalous patterns (multiple failures, unusual hours)

### Secret Management

- **Never** hardcode secrets in source code
- Use environment variables for local development (`.env` in `.gitignore`)
- Use a secrets manager in production: AWS Secrets Manager, HashiCorp Vault, GitHub Actions secrets
- Rotate secrets regularly; revoke immediately if exposed
- Use `git-secrets`, `gitleaks`, or `trufflehog` in pre-commit hooks to catch leaks

```bash
# Scan repo history for secrets
trufflehog git file://. --only-verified

# Scan staged changes
gitleaks detect --staged
```

### Dependency Scanning

Run dependency audits as part of CI:

```bash
# Node.js
npm audit --audit-level=high

# Python
pip-audit

# Docker images
trivy image myapp:latest

# Filesystem (any language)
trivy fs --security-checks vuln .
```

### Secure Coding Patterns

**Rate limiting (Express.js example):**
```js
import rateLimit from 'express-rate-limit';
const loginLimiter = rateLimit({ windowMs: 15 * 60 * 1000, max: 10 });
app.post('/login', loginLimiter, loginHandler);
```

**Parameterised queries:**
```python
# Bad
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
# Good
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

**Security headers (Helmet.js):**
```js
import helmet from 'helmet';
app.use(helmet());
```

## Examples

```bash
# Run full vulnerability scan
trivy fs --exit-code 1 --severity HIGH,CRITICAL .

# Check npm dependencies
npm audit --audit-level=moderate

# Detect secrets in git history
trufflehog git file://. --only-verified --fail

# Generate SBOM for compliance
syft . -o spdx-json > sbom.json
```

## References

- [OWASP Top 10](https://owasp.org/Top10/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [Trivy](https://github.com/aquasecurity/trivy)
- [TruffleHog](https://github.com/trufflesecurity/trufflehog)
- [Gitleaks](https://github.com/gitleaks/gitleaks)
