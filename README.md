# skills-db

A centralized collection of AI agent skills installable via [skillfish](https://skill.fish) — covering Git, Docker, security, testing, DevOps, frontend, and backend development best practices.

## Install

Install all skills at once:
```bash
npx skillfish add Satcomx00-x00/skills-db --all
```

Or install a specific skill:
```bash
npx skillfish add Satcomx00-x00/skills-db/skills/git
npx skillfish add Satcomx00-x00/skills-db/skills/docker
npx skillfish add Satcomx00-x00/skills-db/skills/code-review
npx skillfish add Satcomx00-x00/skills-db/skills/security
npx skillfish add Satcomx00-x00/skills-db/skills/testing
npx skillfish add Satcomx00-x00/skills-db/skills/devops
npx skillfish add Satcomx00-x00/skills-db/skills/frontend
npx skillfish add Satcomx00-x00/skills-db/skills/backend
```

## Team Skill Sync

Add a `skillfish.json` to your project to share skills across your team:

```json
{
  "version": 1,
  "skills": [
    "Satcomx00-x00/skills-db/skills/git",
    "Satcomx00-x00/skills-db/skills/docker",
    "Satcomx00-x00/skills-db/skills/code-review",
    "Satcomx00-x00/skills-db/skills/security",
    "Satcomx00-x00/skills-db/skills/testing",
    "Satcomx00-x00/skills-db/skills/devops",
    "Satcomx00-x00/skills-db/skills/frontend",
    "Satcomx00-x00/skills-db/skills/backend"
  ]
}
```

Then teammates run:
```bash
npx skillfish install
```

## Skills

| Skill | Description |
|-------|-------------|
| [`git`](skills/git/SKILL.md) | Conventional commits, branching strategy, PR rules |
| [`docker`](skills/docker/SKILL.md) | Lean Dockerfiles, multi-stage builds, image security |
| [`code-review`](skills/code-review/SKILL.md) | Review checklist, conventional comments, approval criteria |
| [`security`](skills/security/SKILL.md) | OWASP Top 10, secret management, dependency scanning |
| [`testing`](skills/testing/SKILL.md) | TDD, test pyramid, unit/integration/e2e patterns |
| [`devops`](skills/devops/SKILL.md) | CI/CD pipelines, deployment strategies, observability |
| [`frontend`](skills/frontend/SKILL.md) | Component design, accessibility, Core Web Vitals |
| [`backend`](skills/backend/SKILL.md) | REST API design, auth patterns, database best practices |

## Supported Agents

Skills work with all agents supported by skillfish including Claude Code, Cursor, GitHub Copilot, Windsurf, Codex, Gemini CLI, and [30+ more](https://github.com/knoxgraeme/skillfish#supported-agents).

## Structure

```
skills/
  git/SKILL.md
  docker/SKILL.md
  code-review/SKILL.md
  security/SKILL.md
  testing/SKILL.md
  devops/SKILL.md
  frontend/SKILL.md
  backend/SKILL.md
```

Each skill is a folder containing a `SKILL.md` file with YAML frontmatter (`name`, `description`, `license`, `metadata`) and sections for Instructions, Examples, and References.

## Contributing

1. Create a new folder under `skills/<category-name>/`
2. Add a `SKILL.md` following the format of existing skills
3. Update the table in this README
4. Open a pull request