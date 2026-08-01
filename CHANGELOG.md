# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Phase 0 foundation:
  - `uv` project with Python 3.13 and a `src` layout.
  - Tooling: Ruff, Pyright, pytest, pre-commit, Makefile.
  - Typer CLI (`serve`, `version`, `doctor`, `config`, `plugins`).
  - Hierarchical configuration (defaults → environment YAML → env vars → overrides).
  - DI container, lifecycle manager, and application bootstrap context.
  - structlog-based structured logging.
  - Async event bus with subscriber isolation.
  - Tool framework (`@tool` decorator, metadata, registry, validator, loader).
  - Transport abstraction, registry, and factory (implementations stubbed).
  - MCP protocol/server abstractions.
  - FastAPI REST interface with `/health`, `/live`, `/ready`, `/version`.
  - Scaffolds for extensions, workers, persistence, security, and AI.
  - Docker, docker-compose, Kubernetes manifests, and GitHub Actions CI.
  - Documentation (architecture, design principles, compatibility, ADRs).
