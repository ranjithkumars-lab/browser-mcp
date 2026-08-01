# Design Principles

These principles guide every contribution to this template and to any server
created from it. They keep the codebase consistent, testable, and maintainable
across a family of MCP servers.

1. **Composition over inheritance**
   Prefer composing small, focused objects. Reserve inheritance for stable
   abstraction boundaries (interfaces).

2. **Interface-first design**
   Define the interface before the implementation. Business code depends on
   abstractions (e.g. `Transport`, `MetricsProvider`, `Repository`), never on
   concrete third-party classes.

3. **Async-first where appropriate**
   Use `asyncio` for I/O-bound work. Avoid blocking calls in async code paths.

4. **Transport-independent business logic**
   Domain logic must not import transport or protocol SDKs. This allows new
   transports to be added without touching core services.

5. **Configuration over hardcoding**
   No hardcoded ports, URLs, credentials, or paths. Everything configurable
   via the settings hierarchy (YAML → env → CLI).

6. **Dependency inversion**
   High-level modules define interfaces that low-level modules implement.
   The composition root (`AppContext`) wires them together via DI.

7. **Single responsibility**
   Every module, class, and function has one clear responsibility.

8. **Explicit over implicit**
   Favor explicit wiring and named parameters over magic and global state.
   The DI container is explicit and inspectable.

9. **Fail fast with meaningful errors**
   Validate configuration and inputs early. Raise typed errors with useful
   messages. Never silently swallow exceptions.

10. **Testability by design**
    Every component can be constructed and exercised in isolation. Abstractions
    are small enough to stub, and side effects are injectable.

11. **Scaffold-first development**
    New subsystems are introduced as interfaces and structure first; concrete
    backends (database, metrics, tracing, auth) are added incrementally in
    later phases behind stable extension points.

12. **Template First Principle**
    All new MCP servers must be created from this template. Generic
    capabilities are added here; server-specific capabilities live in the
    individual repository. The template evolves independently, and downstream
    projects adopt new versions through controlled upgrades.
