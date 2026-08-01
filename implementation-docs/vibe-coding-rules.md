# MCP Server Development Rules (Reusable)

## Purpose

These rules define the engineering standards for all MCP Server projects developed with AI assistance.

The objective is to produce production-grade, maintainable, secure, and reusable MCP servers while ensuring that no unintended operations are performed on production environments.

---

# 1. General Principles

- Every MCP server must be production-ready.
- Simplicity is preferred over unnecessary complexity.
- Every component must have a clear responsibility.
- Code must be modular and reusable.
- Avoid hardcoded values.
- Follow clean architecture principles.
- Every feature must be testable.
- Every feature must be documented.

---

# 2. AI Assistant Rules

The AI assistant must follow these rules throughout the project.

## Never assume production state

This repository is a development project.

The AI must never assume:

- deployment succeeded
- Docker is running
- services are available
- firewall is configured
- ports are open
- DNS exists
- SSL exists
- Kubernetes exists
- Redis exists
- PostgreSQL exists

unless the user explicitly confirms them.

---

## Never execute production operations

The AI must **never** instruct the user to directly execute deployment or destructive commands as if they are already complete.

Instead:

- generate commands
- generate scripts
- explain why they are needed

The user will execute them manually.

After execution, the user will provide:

- logs
- screenshots
- terminal output
- errors

Only then should the AI continue.

---

## Never say

Examples of wording to avoid:

- "Deployment is complete."
- "Everything is running."
- "Docker started successfully."
- "The server is healthy."

unless the user has confirmed it.

---

## Always say

Examples of preferred wording:

- "Run the following command."
- "Share the output."
- "Once you provide the result, we'll continue."
- "Verify this step before moving forward."

---

# 3. Phase Completion Rule

Development is phase-based.

Each phase must be fully completed before the next phase begins.

A phase is complete only when:

- implementation finished
- tests passed
- lint passed
- type checking passed
- documentation updated
- examples updated
- user verified locally
- GitHub push completed

Only after all of these are satisfied may the next phase begin.

---

# 4. GitHub Rule

Every completed phase must end with a Git commit and push.

Recommended workflow:

```text
git status
git add .
git commit -m "feat(phase-x): short description"
git push origin main
```

No phase is considered complete until its code is safely stored in GitHub.

---

# 5. No Hidden Changes

The AI must never silently change:

- configuration
- ports
- environment variables
- APIs
- schemas
- security settings

Every important change must be explained.

---

# 6. Production Quality Standard

Every repository should meet these expectations:

- clean architecture
- modular design
- async-first where appropriate
- type hints
- structured logging
- configuration management
- dependency injection where beneficial
- comprehensive error handling
- validation
- unit tests
- integration tests
- documentation

---

# 7. Project Structure Rule

Avoid dumping everything into a single file.

Prefer:

```text
api/
core/
config/
models/
schemas/
services/
plugins/
workers/
storage/
utils/
tests/
docs/
examples/
scripts/
deployments/
```

---

# 8. Configuration Rule

Never hardcode:

- ports
- API URLs
- credentials
- secrets
- file paths

Use:

- environment variables
- configuration files
- defaults that can be overridden

---

# 9. Security Rule

Never hardcode:

- passwords
- API keys
- SSH keys
- tokens

Never expose secrets in logs.

Support secure secret injection through environment variables or external secret managers.

---

# 10. Logging Rule

Every server must use structured logging.

Minimum log levels:

- DEBUG
- INFO
- WARNING
- ERROR
- CRITICAL

Logs should include:

- timestamp
- request ID (where applicable)
- job ID (where applicable)
- duration
- error details

---

# 11. Error Handling Rule

Never silently ignore exceptions.

Errors must:

- be logged
- return meaningful messages
- preserve stack traces for debugging
- avoid exposing sensitive information

---

# 12. Testing Rule

Every major feature requires:

- unit tests
- integration tests

Before phase completion:

- all tests pass
- lint passes
- type checking passes

---

# 13. Documentation Rule

Every phase updates:

- README
- Architecture
- Configuration
- Usage
- Changelog (if maintained)

---

# 14. MCP Compatibility Rule

Every server should support:

- Streamable HTTP transport
- HTTP transport (where applicable)
- SSE transport (optional for legacy compatibility)
- stdio transport (optional for local tooling)

Transport selection must be configurable.

The implementation should separate transport from business logic so additional transports can be added without changing core services.

---

# 15. Default Port Rule

Never hardcode ports.

Example defaults:

```text
MCP_PORT=8000
API_PORT=8080
```

Allow overriding through environment variables or configuration.

---

# 16. Docker Rule

Every project should include:

- Dockerfile
- docker-compose.yml
- .dockerignore

Containers should:

- run as a non-root user
- expose configurable ports
- use health checks where appropriate
- support persistent configuration through mounted volumes

---

# 17. API Rule

If REST APIs are included:

- version endpoints
- OpenAPI enabled
- request validation
- response models
- proper status codes
- pagination where applicable

---

# 18. Plugin Rule

If plugins exist:

Every plugin must contain:

- metadata
- version
- permissions
- input schema
- output schema
- documentation

Plugins should be independently testable.

---

# 19. Code Quality Rule

Use:

- Ruff
- Pyright
- pytest
- pre-commit

Recommended coverage target:

- 90% or higher

---

# 20. Performance Rule

Avoid blocking operations in asynchronous code.

Use:

- connection pooling
- async I/O
- efficient caching where appropriate
- streaming responses when beneficial

---

# 21. Dependency Rule

Keep dependencies minimal.

Prefer mature, actively maintained libraries.

Pin versions for reproducible builds.

---

# 22. User Verification Rule

The AI must pause after important milestones.

The workflow is:

1. AI generates code.
2. User runs it locally.
3. User shares output.
4. AI analyzes results.
5. AI proposes fixes if required.
6. Continue only after verification.

---

# 23. Breaking Change Rule

Breaking changes require:

- explanation
- migration steps
- version update
- documentation update

---

# 24. Release Rule

Before any release:

- tests pass
- documentation complete
- examples verified
- lint clean
- type checking clean
- Docker build verified
- user validation completed

---

# 25. Completion Checklist

A phase is complete only if all items are checked:

- Feature implemented
- Tests passing
- Lint passing
- Type checking passing
- Documentation updated
- Examples updated
- Configuration reviewed
- User verified locally
- Git committed
- Git pushed to GitHub

Only then may development proceed to the next phase.

---

# Guiding Principle

The AI acts as an engineering partner, not an operator.

It designs, explains, generates code, reviews results, and recommends changes.

The user remains responsible for executing commands, validating environments, deploying systems, and confirming outcomes before the next step proceeds.
