---
name: code-review
description: Code review standards and checklist — how to give constructive feedback, what to look for, and how to approve or request changes effectively. Use this skill whenever someone asks to review code, provide feedback on a pull request, check code for bugs or issues, evaluate a PR, audit code quality, or says things like "can you look at this code", "what's wrong with this", or "is this code good" — even if they don't use the phrase "code review".
license: MIT
metadata:
  author: Satcomx00-x00
  version: 2.0.0
---

# code-review

Code review standards and checklist — how to give constructive feedback, what to look for, and how to approve or request changes effectively.

## Workflow

When reviewing code (as an agent or assisting a human reviewer):

1. **Understand intent** — read the PR description / commit message first; understand what the change is trying to achieve before reading the diff
2. **Scan for blocking issues** — check type safety, error handling, and security first (these must be resolved before merge)
3. **Apply the checklist** — work through Correctness → Security → Performance → Readability → Tests → Dependencies
4. **Label every comment** — use `issue:` (blocking), `suggestion:` (improvement), `nit:` (minor), `question:` (clarification), `praise:` (positive)
5. **Summarise at the top** — give an overall verdict with a list of blocking issues so the author knows immediately what must change

**Output format:**
```
## Review Summary
Verdict: [Approve | Request changes | Comment]
Blocking issues: (list any issue: comments here)
Suggestions: (list key suggestions)
```

## Guidelines

When reviewing code, the following quality rules apply. Items marked **blocking** must be resolved before approval.

### Type Safety (blocking)

- [ ] No `any` types introduced without a documented justification
- [ ] All new functions have explicit parameter and return type annotations
- [ ] Data from external sources (API, env vars, DB) is validated with a typed schema before use
- [ ] No non-null assertions (`!`) without an adjacent guard or a comment explaining why it is safe

### Error Handling (blocking)

- [ ] No empty `catch` blocks or silently swallowed exceptions
- [ ] Errors propagate with enough context to diagnose in production (relevant IDs, operation name)
- [ ] All async operations have error handling — no un-awaited promises without `.catch()`

### Code Quality (advisory)

- [ ] Functions are ≤ 30 lines and have a single responsibility
- [ ] No commented-out code committed to the branch
- [ ] Public API surface (functions, classes, endpoints) has doc-comments
- [ ] Names express intent — no single-letter variables outside of loop indices
- [ ] No magic numbers or strings — use named constants

---

### Review Checklist

**Correctness**
- [ ] Does the code do what the PR description says it does?
- [ ] Are edge cases handled (null/empty/zero/large input)?
- [ ] Are error paths handled and surfaced correctly?
- [ ] Are there race conditions or concurrency issues?
- [ ] Are external API calls resilient (retries, timeouts, error handling)?

**Security**
- [ ] No secrets, tokens, or credentials hardcoded
- [ ] User input is validated and sanitised
- [ ] SQL queries use parameterised statements (no string interpolation)
- [ ] File paths are validated to prevent path traversal
- [ ] Authentication and authorisation checks are in place

**Performance**
- [ ] No N+1 query patterns — use batch/eager loading where needed
- [ ] Expensive operations cached where appropriate
- [ ] No unnecessary re-renders or re-computations in hot paths
- [ ] Large loops or data structures don't blow up memory

**Readability & Maintainability**
- [ ] Variable and function names clearly convey intent
- [ ] Functions do one thing (Single Responsibility Principle)
- [ ] Complex logic has explanatory comments (the *why*, not the *what*)
- [ ] No dead code or commented-out blocks left in
- [ ] DRY — no copy-pasted logic that should be extracted

**Tests**
- [ ] New functionality has corresponding tests
- [ ] Tests cover happy paths and important edge cases
- [ ] Tests are deterministic (no reliance on system time, random, network)
- [ ] Existing tests still pass

**Dependencies**
- [ ] New dependencies are justified and actively maintained
- [ ] Dependency versions are pinned or constrained appropriately
- [ ] No license conflicts introduced

### Giving Feedback

Use the **conventional comment** format for clarity:

```
<label>: <message>
```

**Labels:**
- `nit:` – minor style preference, non-blocking
- `suggestion:` – improvement idea, non-blocking
- `question:` – seeking understanding, non-blocking
- `issue:` – must fix before merge (blocking)
- `praise:` – positive feedback, encourage good patterns

**Example comments:**
```
nit: variable name `d` could be more descriptive — `durationMs` perhaps?

issue: this function doesn't handle the case where `user` is null,
       which will throw when called from the admin panel.

suggestion: extracting this loop into a `groupByCategory()` helper would
            make it reusable and easier to test.

praise: great use of the strategy pattern here — this will be easy to extend!
```

### Approval Criteria

- **Approve** when all blocking issues are resolved and the code is production-ready
- **Request changes** when there are blocking `issue:` comments
- **Comment** (no approval/rejection) for questions or discussion
- Aim to complete reviews within 24 hours of assignment

### As an Agent

When asked to review code:
1. Apply the checklist above systematically
2. Group feedback by category (correctness, security, performance, etc.)
3. Clearly distinguish blocking issues from suggestions
4. Provide specific, actionable comments with examples where possible
5. Summarise findings at the top: overall verdict + list of blocking issues

## Examples

**Review summary format:**
```
## Review Summary

**Verdict:** Request changes

**Blocking issues:**
1. Line 42: SQL injection vulnerability — use parameterised query
2. Line 87: Missing null check before accessing `user.profile`

**Suggestions:**
- Consider extracting the retry logic into a shared utility
- The timeout on line 105 (30s) seems high for a user-facing request

**Nits:**
- Prefer `const` over `let` for `result` (never reassigned)
```

## References

- [Conventional Comments](https://conventionalcomments.org/)
- [Google Engineering Practices — Code Review](https://google.github.io/eng-practices/review/)
- [The Art of Giving and Receiving Code Reviews](https://www.alexandra-hill.com/2018/06/25/the-art-of-giving-and-receiving-code-reviews/)
