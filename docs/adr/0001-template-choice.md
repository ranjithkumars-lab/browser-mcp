# ADR 0001: Template-first Enterprise MCP Foundation

- **Status:** Accepted
- **Date:** 2026-08-01

## Context

The organization builds a family of MCP servers (browser automation, scraping,
form automation, RPA, API testing). Without shared infrastructure, each server
would reinvent configuration, logging, transports, and tooling, leading to
architecture drift and maintenance burden.

## Decision

Create an **enterprise MCP server template** with zero business logic that
provides infrastructure, abstractions, and tooling. Adopt the **Template First
Principle**: all new MCP servers are created from the template. Generic
capabilities are added to the template; server-specific capabilities remain in
the individual repository. The template evolves independently, and downstream
projects adopt new versions through controlled upgrades.

## Consequences

- Consistent architecture and tooling across the MCP server family.
- Template changes benefit all downstream servers.
- Downstream servers must manage template version upgrades deliberately.
- Browser automation and other domain SDKs must never be imported into the
  template.
