from browser_mcp.errors import BrowserError


class PluginError(BrowserError):
    pass


class PluginNotFoundError(PluginError):
    pass


class PluginManifestError(PluginError):
    pass


class PluginDependencyError(PluginError):
    pass


class CircularDependencyError(PluginDependencyError):
    pass


class PluginPermissionDeniedError(PluginError):
    pass


class PluginSignatureError(PluginError):
    pass


class PluginSchemaValidationError(PluginError):
    pass


class PluginLifecycleError(PluginError):
    pass


class PluginExecutionError(PluginError):
    pass
