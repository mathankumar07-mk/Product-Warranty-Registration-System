"""Central application exceptions.

Route handlers should translate these to HTTP responses so business
logic in services stays framework-agnostic and safe to reuse.
"""

from __future__ import annotations


class AppError(Exception):
    """Base class for expected domain errors."""


class NotFoundError(AppError):
    """Requested resource does not exist or is not visible to caller."""


class ConflictError(AppError):
    """Request conflicts with current state (duplicate, illegal transition)."""


class ForbiddenError(AppError):
    """Caller is not allowed to access or mutate the resource."""


class ValidationError(AppError):
    """Request data failed business-rule validation."""
