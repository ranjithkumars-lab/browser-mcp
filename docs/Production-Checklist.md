# Production Checklist

Use this checklist before deploying any server created from the template to a
production environment.

## Configuration

- [ ] Secrets are injected via environment variables or a secret manager.
- [ ] `ENTERPRISE_MCP_ENV=production` is set.
- [ ] `debug` is `false`.
- [ ] Bind host and port are configured explicitly.
- [ ] Logging format is `json`.
- [ ] Metrics and tracing are enabled with real backends.

## Security

- [ ] Authentication is enabled (`server.security.enabled: true`).
- [ ] A real auth provider is configured (not `none`).
- [ ] RBAC is enforced for tool execution.
- [ ] Audit logging is enabled and exported.
- [ ] No secrets appear in logs.
- [ ] TLS is terminated at the ingress / reverse proxy.

## Availability

- [ ] `/health`, `/live`, `/ready` are wired into orchestration probes.
- [ ] Readiness reflects real dependency state.
- [ ] Graceful shutdown is configured and verified.
- [ ] Restart policy / replicas are configured (Docker/K8s).

## Reliability

- [ ] Retry policies are configured for external calls.
- [ ] Worker queues have dead-letter handling (when workers are enabled).
- [ ] Backups / disaster recovery are in place for persistent data.

## Observability

- [ ] Structured logs are collected and indexed.
- [ ] Metrics are exported (Prometheus/OpenTelemetry backend implemented).
- [ ] Distributed tracing is enabled where required.
- [ ] Error budgets / alerts are defined.

## Testing & Release

- [ ] Full test suite passes.
- [ ] Lint passes.
- [ ] Type checking passes.
- [ ] Docker image builds successfully.
- [ ] Image is scanned for vulnerabilities.
- [ ] Release notes / changelog updated.
- [ ] Breaking changes documented with migration steps.

## Operations

- [ ] Runbook / troubleshooting guide exists.
- [ ] Capacity planning done (browsers, workers, storage).
- [ ] Load/stress test performed.
- [ ] Rollback strategy defined.
