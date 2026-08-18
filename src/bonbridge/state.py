"""Small persistent key/value store for runtime facts.

Separate from the configuration on purpose: ``config.yaml`` holds what the user
decided, this file holds what the device learned.  It survives a reboot or a
power cut, which is what makes "a cash drawer was seen on this printer" and
"the paper-low warning was already printed" behave sensibly.

Stored as JSON in ``/var/lib/bonbridge/state.json`` and written atomically, so
pulling the plug mid-write cannot leave a truncated file behind.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
from typing import Any, Dict, Optional

from . import paths

log = logging.getLogger(__name__)

_LOCK = threading.RLock()
_CACHE: Optional[Dict[str, Any]] = None


def _path():
    return paths.STATE_DIR / "state.json"


def load() -> Dict[str, Any]:
    global _CACHE
    with _LOCK:
        if _CACHE is not None:
            return _CACHE
        try:
            with open(_path(), "r", encoding="utf-8") as handle:
                data = json.load(handle)
            _CACHE = data if isinstance(data, dict) else {}
        except FileNotFoundError:
            _CACHE = {}
        except Exception as exc:  # noqa: BLE001 - a corrupt file must not stop the daemon
            log.warning("Cannot read %s (%s) - starting with empty state", _path(), exc)
            _CACHE = {}
        return _CACHE


def save() -> None:
    with _LOCK:
        data = load()
        target = _path()
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), prefix=".state-", suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=1, ensure_ascii=False)
            os.replace(tmp_name, target)
        except Exception as exc:  # noqa: BLE001
            log.warning("Cannot write %s: %s", target, exc)


def get(section: str, key: str, default: Any = None) -> Any:
    with _LOCK:
        return (load().get(section) or {}).get(key, default)


def set_value(section: str, key: str, value: Any, persist: bool = True) -> None:
    with _LOCK:
        data = load()
        bucket = data.setdefault(section, {})
        if bucket.get(key) == value:
            return
        bucket[key] = value
        if persist:
            save()


def section(name: str) -> Dict[str, Any]:
    with _LOCK:
        return dict(load().get(name) or {})


def reset() -> None:
    """Only used by the tests."""
    global _CACHE
    with _LOCK:
        _CACHE = {}
