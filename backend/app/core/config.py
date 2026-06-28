"""
Backwards-compatible re-export of Settings/get_settings from app.core.settings.

What it does:
- Lets older code keep writing `from app.core.config import get_settings`
  while the real definition lives in app.core.settings.
- Acts as a one-stop import shim — no logic of its own.

Upstream (who imports this): legacy call sites that still reference app.core.config
(none currently in repo, but kept as a stable public surface).
Downstream (what this imports): app.core.settings (Settings class + cached factory).
"""
# Settings, get_settings: re-exported so `from app.core.config import ...` keeps working
from app.core.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
