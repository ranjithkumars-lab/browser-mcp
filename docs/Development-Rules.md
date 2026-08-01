# Development Rules

These rules define the engineering standards for this repository and for every
server created from the template.

## 1. General Principles

- Production-ready quality is the default, not the goal.
- Simplicity over unnecessary complexity.
- Every component has a single clear responsibility.
- Code must be modular and reusable.
- No hardcoded values; use configuration.
- Clean architecture and explicit wiring.
- Every feature must be testable and documented.

## 2. Phase Completion

Development is phase-based. A phase is complete only when:

- implementation is finished
- tests pass
- lint passes
- type checking passes
- documentation is updated
- examples are updated
- the user verified the work locally
- the commit is pushed to GitHub

Only then may the next phase begin.

## 3. Git / GitHub

Every completed phase ends with a commit and push:

```text
git status
git add .
git commit -m "feat(phase-x): short description"
git push origin main
```

No phase is complete until its code is safely stored in GitHub.

## 4. No Hidden Changes

Never silently change configuration, ports, environment variables, APIs,
schemas, or security settings. Every important change is explained.

## 5. Configuration

Never hardcode:

- ports
- API URLs
- credentials / secrets
- file paths

Use environment variables, configuration files, and overridable defaults.

## 6. Security

- Never hardcode passwords, API keys, SSH keys, or tokens.
- Never expose secrets in logs.
- Support secure secret injection via environment variables or external
  secret managers.

## 7. Logging

- Structured logging only (this template uses `structlog`).
- Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.
- Logs include timestamp, request/job IDs where applicable, duration, and
  error details.

## 8. Error Handling

- Never silently ignore exceptions.
- Errors are logged, return meaningful messages, preserve stack traces, and
  avoid exposing sensitive information.
- Use the typed error hierarchy in `enterprise_mcp.utils.errors`.

## 9. Testing

Every major feature requires unit tests (and integration tests where
appropriate). Before phase completion:

- all tests pass
- lint passes
- type checking passes

## 10. Documentation

Every phase updates: README, Architecture, Configuration, Usage, Changelog.

## 11. Code Quality

- Ruff (lint + format)
- Pyright (strict type checking)
- pytest
- pre-commit

## 12. Dependencies

- Keep dependencies minimal.
- Prefer mature, actively maintained libraries.
- Pin versions with upper bounds for reproducible builds.

## 13. AI Assistant Rules

When an AI assistant works in this repository:

- **Never assume production state** — deployment, services, ports, DNS, TLS,
  and infrastructure are never assumed to be running.
- **Never execute production operations** — generate commands and scripts;
  the user executes them and shares output before work continues.
- **Pause after milestones** — generate code, user runs it, user shares output,
  AI analyzes, fixes are proposed, continue only after verification.

## 14. Breaking Changes

Breaking changes require an explanation, migration steps, a version update,
and documentation updates.

## 15. Release

Before any release: tests pass, documentation complete, examples verified,
lint clean, type checking clean, Docker build verified, user validation done.
