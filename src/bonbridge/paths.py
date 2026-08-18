"""Filesystem locations used by BonBridge.

Everything is overridable through environment variables so the daemon can be
run straight from a git checkout (development) as well as from the installed
location (/opt/bonbridge).
"""

from __future__ import annotations

import os
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _env_path(name: str, default: Path) -> Path:
    value = os.environ.get(name)
    return Path(value).expanduser() if value else default


#: Directory containing the installed source tree (``.../src/bonbridge``).
PACKAGE_DIR: Path = _HERE

#: Repository / installation root (contains ``src/``, ``vendor/``, ``docs/``).
ROOT_DIR: Path = _env_path("BONBRIDGE_ROOT", _HERE.parent.parent)

#: Writable configuration directory.
CONFIG_DIR: Path = _env_path("BONBRIDGE_CONFIG_DIR", Path("/etc/bonbridge"))

#: Main configuration file.
CONFIG_FILE: Path = _env_path("BONBRIDGE_CONFIG", CONFIG_DIR / "config.yaml")

#: Variable state: spool files, detected capabilities, counters.
STATE_DIR: Path = _env_path("BONBRIDGE_STATE_DIR", Path("/var/lib/bonbridge"))

#: Spooled print jobs that could not be delivered yet.
SPOOL_DIR: Path = STATE_DIR / "spool"

#: Log directory (the daemon also logs to journald when run under systemd).
LOG_DIR: Path = _env_path("BONBRIDGE_LOG_DIR", Path("/var/log/bonbridge"))

#: Vendored third-party data (escpos-printer-db, zj-58).
VENDOR_DIR: Path = _env_path("BONBRIDGE_VENDOR_DIR", ROOT_DIR / "vendor")

#: Built-in printer profiles maintained by this project.
PROFILE_DIR: Path = PACKAGE_DIR / "profiles"

#: Static assets for the web interface.
WEB_STATIC_DIR: Path = PACKAGE_DIR / "web" / "static"

#: Documentation tree (served read-only by the web interface).
DOCS_DIR: Path = _env_path("BONBRIDGE_DOCS_DIR", ROOT_DIR / "docs")


def ensure_runtime_dirs() -> None:
    """Create the writable directories the daemon needs."""
    for directory in (CONFIG_DIR, STATE_DIR, SPOOL_DIR, LOG_DIR):
        directory.mkdir(parents=True, exist_ok=True)
