# Folder Structure

## Root Layout

```text
enterprise-mcp-server-template/
├── src/enterprise_mcp/          # application source package
├── tests/                       # unit, integration, e2e, fixtures, data
├── examples/                    # basic, advanced, production examples
├── scripts/                     # bootstrap, release, version, docs, docker, dev
├── docs/                        # architecture, rules, ADRs, diagrams
├── deployments/                 # docker, kubernetes
├── .github/                     # workflows, templates, CODEOWNERS, SECURITY
├── Makefile                     # developer experience commands
├── pyproject.toml               # uv + tooling configuration
├── .pre-commit-config.yaml      # git hooks
└── README.md
```

## Source Package

```text
src/enterprise_mcp/
├── __init__.py
├── foundation/     # container.py, lifecycle.py, app.py
├── config/         # models.py, loader.py, defaults.py, paths.py, settings/*.yaml
├── observability/  # logging/, metrics/, tracing/
├── security/       # auth.py, rbac.py, secrets.py, audit.py
├── transport/      # base.py, http.py, sse.py, stdio.py, registry.py, factory.py
├── mcp/            # protocol/, server/
├── tools/          # decorators.py, metadata.py, loader.py, validator.py, registry.py
├── extensions/     # base.py, registry.py, middleware/, plugins/, hooks/, providers/
├── workers/        # base.py, retry.py, executors/, queues/
├── persistence/    # base.py, repositories/, models/, migrations/, database/
├── interfaces/     # rest/, websocket/, internal/
├── events/         # types.py, bus.py
├── resources/      # templates/, static/, sample-data/
├── utils/          # errors.py, version.py
├── ai/             # memory/, prompts/, agents/ (reserved)
└── cli/            # main.py, commands/
```

## Tests

```text
tests/
├── conftest.py             # shared fixtures + pytest_configure hook
├── unit/                   # focused, isolated tests
├── integration/            # component integration tests (later phases)
├── e2e/                    # end-to-end tests (later phases)
├── fixtures/               # shared fixture helpers
└── data/                   # test data files
```

## Documentation

```text
docs/
├── index.md                # mkdocs landing page
├── Architecture.md
├── Design-Principles.md
├── Compatibility.md
├── Development-Rules.md
├── Folder-Structure.md
├── Production-Checklist.md
├── adr/                    # Architecture Decision Records
└── diagrams/               # architecture diagrams
```

## Deployment

```text
deployments/
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.dev.yml
│   └── docker-compose.prod.yml
└── kubernetes/
    ├── deployment.yaml
    ├── service.yaml
    ├── configmap.yaml
    └── README.md
```

## GitHub

```text
.github/
├── workflows/
│   ├── ci.yml
│   └── release.yml
├── ISSUE_TEMPLATE/
├── PULL_REQUEST_TEMPLATE.md
├── CODEOWNERS
└── SECURITY.md
```
