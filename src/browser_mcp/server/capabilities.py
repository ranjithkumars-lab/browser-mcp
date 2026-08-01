class CapabilityRegistry:
    def __init__(
        self,
        *,
        tools: bool = True,
        notifications: bool = True,
        resources: bool = False,
        prompts: bool = False,
    ) -> None:
        self._capabilities = {
            "tools": tools,
            "notifications": notifications,
            "resources": resources,
            "prompts": prompts,
        }

    def negotiate(self, client: dict[str, object] | None = None) -> dict[str, object]:
        return {
            name: {}
            for name, enabled in self._capabilities.items()
            if enabled and (not client or client.get(name, True))
        }
