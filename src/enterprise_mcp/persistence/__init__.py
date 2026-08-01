"""Persistence subsystem scaffolds.

Repositories, models, migrations, and database drivers are implemented in
later phases. Phase 0 defines the interfaces only; no third-party drivers
are imported.
"""

from enterprise_mcp.persistence.base import Repository
from enterprise_mcp.persistence.models.base import Entity

__all__ = ["Entity", "Repository"]
