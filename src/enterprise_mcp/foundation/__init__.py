"""Foundation subsystem.

Contains the dependency injection container, application lifecycle
management, and the application bootstrap context.
"""

from enterprise_mcp.foundation.app import AppContext
from enterprise_mcp.foundation.container import Container, DependencyError
from enterprise_mcp.foundation.lifecycle import LifecycleManager

__all__ = ["AppContext", "Container", "DependencyError", "LifecycleManager"]
