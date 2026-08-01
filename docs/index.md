# Enterprise MCP Server Template

Welcome to the documentation for the Enterprise MCP Server Template.

A production-ready, transport-independent foundation for building enterprise
Model Context Protocol (MCP) servers in Python. This template contains zero
business logic — downstream servers fork it and add their own capabilities.

## Contents

- [Architecture](Architecture.md)
- [Design Principles](Design-Principles.md)
- [Compatibility](Compatibility.md)
- [Development Rules](Development-Rules.md)
- [Folder Structure](Folder-Structure.md)
- [Production Checklist](Production-Checklist.md)
- [Architecture Decision Records](adr/index.md)
- [Navigation Engine](navigation/overview.md)
- [Element Engine](elements/overview.md)
- [Plugins](plugins/creating-plugin.md)
- [Form Automation](forms/overview.md)

## Quick Start

```bash
uv sync --all-extras
uv run enterprise-mcp doctor
uv run enterprise-mcp serve
```
