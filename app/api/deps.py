"""Compatibility dependency module for the mandatory v1 layout.

The existing flat routers import from ``app.core.dependencies``.
New ``app/api/v1`` code should import from here to match the reference
architecture without breaking existing imports.
"""

from app.core.dependencies import DBSession, get_current_admin, get_current_user

__all__ = ["DBSession", "get_current_admin", "get_current_user"]
