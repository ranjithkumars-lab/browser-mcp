# Security Policy

## Supported Versions

Only the latest release receives security updates.

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |
| older   | :x:                |

## Reporting a Vulnerability

Please do **not** open a public issue for security vulnerabilities. Report them
privately to the maintainers:

- Open a private advisory via GitHub: **Security → Report a vulnerability**.
- Or email the maintainers directly.

Include:

- Affected versions.
- Steps to reproduce.
- Impact assessment, if known.

You will receive an acknowledgement within 3 business days, and we will work
with you on a fix and coordinated disclosure.

## Security Guidelines

- Never hardcode secrets (API keys, passwords, tokens) in code.
- Never expose secrets in logs.
- Support secret injection via environment variables or secret managers.
- Report any accidental exposure of credentials immediately.
