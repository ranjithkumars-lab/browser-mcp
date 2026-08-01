# Authentication Examples

## 1. Form Login

Log in to a web application using the `form` strategy.

```python
from browser_mcp.auth.models import AuthCredentials
from browser_mcp.auth.strategies.registry import AuthStrategyRegistry
from browser_mcp.auth.strategies.form import FormAuthStrategy
from browser_mcp.auth.storage.manager import AuthStorageManager
from browser_mcp.auth.storage.encryption import AuthEncryptionEngine
from browser_mcp.auth.provider import PlaywrightAuthProvider
from browser_mcp.auth.manager import AuthManager
from enterprise_mcp.events.bus import EventBus

registry = AuthStrategyRegistry()
registry.register(FormAuthStrategy())
storage = AuthStorageManager(
    directory="~/.browser-mcp/auth_states",
    encryption=AuthEncryptionEngine(key="my-secret"),
)
auth_manager = AuthManager(
    registry=registry,
    storage=storage,
    provider=PlaywrightAuthProvider(),
    event_bus=EventBus(),
)

credentials = AuthCredentials(
    username="alice",
    password="s3cret",
    url="https://app.example.com/login",
    strategy="form",
    metadata={"context_id": "ctx-1", "session_id": "ses-1"},
)

result = await auth_manager.login(page, credentials)
print(result["success"])  # True
```

## 2. Cookie Injection

Inject cookies directly into a context.

```python
credentials = AuthCredentials(
    url="https://app.example.com",
    strategy="cookie",
    cookies={"session_id": "abc123", "user": "alice"},
    metadata={"context_id": "ctx-1", "session_id": "ses-1"},
)

result = await auth_manager.login(context, credentials)
```

## 3. Header Injection

Inject JWT or API key headers.

```python
credentials = AuthCredentials(
    url="https://api.example.com",
    strategy="header",
    headers={"Authorization": "Bearer eyJhbGciOi..."},
    metadata={"context_id": "ctx-1", "session_id": "ses-1"},
)

result = await auth_manager.login(context, credentials)
```

## 4. State Persistence

Save and reload auth state across server restarts.

```python
# Save
state = await auth_manager.load_state("ctx-1")
await auth_manager.save_state("ctx-1", "ses-1", state)

# Later...
reloaded = await auth_manager.load_state("ctx-1")
```

## 5. Custom Strategy

Register a custom strategy.

```python
class MyCustomStrategy(BaseAuthStrategy):
    @property
    def name(self) -> str:
        return "custom"

    async def execute(self, context, credentials):
        # custom logic
        return {"success": True}

registry.register(MyCustomStrategy())
```
