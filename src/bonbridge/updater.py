"""Software updates: check GitHub, install online, or install an uploaded file.

Three ways in, one installation path:

* ``bonbridge update`` on the console - checks, shows the release notes, asks
  once, then installs with live output.
* the web interface - same thing with a confirmation dialog and the installer
  output streamed into the page.
* an uploaded archive - for devices with no internet access at all: download
  the release on any machine, upload the file here, install.

All three end in the repository's own ``install.sh``, which is the only piece
that knows how to lay the files down.  Nothing here reimplements it.

Two details that are easy to get wrong and are handled deliberately:

**The installer restarts the service that started it.** When the update is
triggered from the web interface, the process running the installer is a child
of the daemon, and ``systemctl restart bonbridge`` kills the whole control
group - including that child, mid-copy.  The update is therefore launched
through ``systemd-run`` as a separate transient unit whenever systemd is
available, so it survives the restart of the thing that started it.

**A bad update must not leave a dead device behind.** The previous
installation is packed into a tarball first; ``bonbridge update --rollback``
puts it back.

References
----------
* GitHub releases API: https://docs.github.com/en/rest/releases/releases
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import threading
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import __version__, paths

log = logging.getLogger(__name__)

USER_AGENT = f"BonBridge/{__version__} (+https://github.com/loe17/Bonbridge)"

#: Largest archive we accept, uploaded or downloaded.  A release tarball is a
#: few hundred kilobytes; anything far beyond that is not a BonBridge release.
MAX_ARCHIVE_BYTES = 40 * 1024 * 1024

#: Files that must be present for an archive to be a plausible BonBridge tree.
REQUIRED_MEMBERS = ("install.sh", "src/bonbridge/__init__.py", "VERSION")


# --------------------------------------------------------------------------
# Versions
# --------------------------------------------------------------------------


def parse_version(text: str) -> Tuple[int, ...]:
    """``"v1.2.3"`` -> ``(1, 2, 3)``.  Unparsable input sorts lowest."""
    match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", str(text or ""))
    if not match:
        return (0,)
    return tuple(int(part) for part in match.groups(default="0"))


def is_newer(candidate: str, current: str = __version__) -> bool:
    return parse_version(candidate) > parse_version(current)


# --------------------------------------------------------------------------
# Status file - shared between the daemon and the detached installer
# --------------------------------------------------------------------------


def log_file() -> Path:
    return paths.LOG_DIR / "update.log"


def status_file() -> Path:
    return paths.UPDATE_DIR / "status.json"


def write_status(**fields: Any) -> Dict[str, Any]:
    data = read_status()
    data.update(fields)
    data["updated_at"] = time.time()
    try:
        paths.UPDATE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = status_file().with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
        os.replace(tmp, status_file())
    except OSError as exc:
        log.warning("Cannot write the update status: %s", exc)
    return data


def read_status() -> Dict[str, Any]:
    try:
        with open(status_file(), "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def tail_log(lines: int = 200) -> str:
    try:
        with open(log_file(), "r", encoding="utf-8", errors="replace") as handle:
            content = handle.readlines()
    except OSError:
        return ""
    return "".join(content[-lines:])


def append_log(text: str) -> None:
    try:
        paths.LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(log_file(), "a", encoding="utf-8") as handle:
            handle.write(text if text.endswith("\n") else text + "\n")
    except OSError:
        pass


# --------------------------------------------------------------------------
# Checking GitHub
# --------------------------------------------------------------------------


def _get_json(url: str, timeout: float = 10.0) -> Any:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed https URL
        return json.loads(response.read().decode("utf-8"))


def check(repository: str = "loe17/Bonbridge", timeout: float = 10.0) -> Dict[str, Any]:
    """Ask GitHub for the newest published release.

    Only tagged releases are considered - never the moving ``main`` branch, so
    what lands on a device is always something that was deliberately released.
    """
    result: Dict[str, Any] = {
        "ok": False,
        "current": __version__,
        "latest": "",
        "update_available": False,
        "checked_at": time.time(),
        "repository": repository,
    }
    url = f"https://api.github.com/repos/{repository}/releases/latest"
    try:
        data = _get_json(url, timeout)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            # A pushed git tag is not automatically a GitHub *release*, and
            # "git tag -a v1.2.3 && git push origin v1.2.3" is how this project
            # is actually versioned - so fall back to the tag list instead of
            # reporting "no updates" to someone who just published one.
            return _check_tags(repository, result, timeout)
        if exc.code in (403, 429):
            result["error"] = (
                "GitHub hat die Anfrage abgelehnt (Limit fuer unangemeldete Zugriffe). "
                "Spaeter erneut versuchen. / GitHub refused the request (unauthenticated "
                "rate limit) - try again later."
            )
        else:
            result["error"] = f"GitHub: HTTP {exc.code}"
        return result
    except Exception as exc:  # noqa: BLE001 - offline is a normal state here
        result["error"] = str(exc)
        return result

    tag = str(data.get("tag_name") or "")
    result.update(
        {
            "ok": True,
            "latest": tag.lstrip("vV"),
            "tag": tag,
            "name": data.get("name") or tag,
            "published_at": data.get("published_at") or "",
            "notes": (data.get("body") or "")[:8000],
            "html_url": data.get("html_url") or "",
            "tarball_url": data.get("tarball_url") or "",
            "update_available": bool(tag) and is_newer(tag),
        }
    )
    return result


def _check_tags(repository: str, result: Dict[str, Any], timeout: float) -> Dict[str, Any]:
    """Newest version tag, for repositories without GitHub release entries."""
    try:
        tags = _get_json(f"https://api.github.com/repos/{repository}/tags?per_page=100", timeout)
    except Exception as exc:  # noqa: BLE001
        result["error"] = str(exc)
        return result
    if not isinstance(tags, list) or not tags:
        result["ok"] = True
        result["error"] = "Es gibt noch keine Versionen / no versions published yet"
        return result
    best = max(tags, key=lambda entry: parse_version(entry.get("name", "")))
    tag = str(best.get("name") or "")
    result.update(
        {
            "ok": True,
            "latest": tag.lstrip("vV"),
            "tag": tag,
            "name": tag,
            "source": "tags",
            "notes": "",
            "html_url": f"https://github.com/{repository}/releases/tag/{tag}",
            "tarball_url": best.get("tarball_url") or "",
            "update_available": bool(tag) and is_newer(tag),
        }
    )
    return result


def download(url: str, destination: Path, timeout: float = 60.0) -> Path:
    """Download a release archive, refusing anything implausibly large."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        declared = int(response.headers.get("Content-Length") or 0)
        if declared > MAX_ARCHIVE_BYTES:
            raise ValueError(f"archive is too large ({declared} bytes)")
        written = 0
        with open(destination, "wb") as handle:
            while True:
                chunk = response.read(65536)
                if not chunk:
                    break
                written += len(chunk)
                if written > MAX_ARCHIVE_BYTES:
                    raise ValueError("archive is too large")
                handle.write(chunk)
    return destination


# --------------------------------------------------------------------------
# Archives
# --------------------------------------------------------------------------


def _safe_extract_tar(archive: tarfile.TarFile, target: Path) -> None:
    """Extract without letting a member escape the target directory."""
    root = target.resolve()
    for member in archive.getmembers():
        destination = (target / member.name).resolve()
        if not str(destination).startswith(str(root)):
            raise ValueError(f"archive member escapes the target directory: {member.name}")
        if member.issym() or member.islnk():
            raise ValueError(f"archive contains a link: {member.name}")
    archive.extractall(target)  # noqa: S202 - members validated above


def _safe_extract_zip(archive: zipfile.ZipFile, target: Path) -> None:
    root = target.resolve()
    for name in archive.namelist():
        destination = (target / name).resolve()
        if not str(destination).startswith(str(root)):
            raise ValueError(f"archive member escapes the target directory: {name}")
    archive.extractall(target)  # noqa: S202 - members validated above


def extract(archive_path: Path, target: Path) -> Path:
    """Unpack an archive and return the directory that holds ``install.sh``."""
    target.mkdir(parents=True, exist_ok=True)
    name = archive_path.name.lower()
    if name.endswith((".tar.gz", ".tgz", ".tar")):
        with tarfile.open(archive_path, "r:*") as archive:
            _safe_extract_tar(archive, target)
    elif name.endswith(".zip"):
        with zipfile.ZipFile(archive_path) as archive:
            _safe_extract_zip(archive, target)
    else:
        # Sniff instead of trusting the file name - browsers rename downloads.
        try:
            with tarfile.open(archive_path, "r:*") as archive:
                _safe_extract_tar(archive, target)
        except tarfile.TarError:
            with zipfile.ZipFile(archive_path) as archive:
                _safe_extract_zip(archive, target)
    return find_source_root(target)


def find_source_root(target: Path) -> Path:
    """The directory inside an unpacked archive that is the repository root."""
    candidates = [target] + sorted(p for p in target.iterdir() if p.is_dir())
    for candidate in candidates:
        if all((candidate / member).exists() for member in REQUIRED_MEMBERS):
            return candidate
    raise ValueError(
        "the archive does not look like a BonBridge release "
        "(install.sh, src/bonbridge and VERSION are missing)"
    )


def archive_version(source_root: Path) -> str:
    try:
        return (source_root / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return ""


# --------------------------------------------------------------------------
# Backup and rollback
# --------------------------------------------------------------------------


def backup(install_dir: Optional[Path] = None, keep: int = 3) -> Optional[Path]:
    """Pack the current installation so a bad update can be undone."""
    root = Path(install_dir or paths.ROOT_DIR)
    if not (root / "src" / "bonbridge").is_dir():
        log.info("Nothing to back up at %s", root)
        return None
    paths.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    target = paths.BACKUP_DIR / f"bonbridge-{__version__}-{stamp}.tar.gz"
    with tarfile.open(target, "w:gz") as archive:
        for name in ("src", "vendor", "docs", "packaging", "VERSION", "install.sh", "uninstall.sh"):
            item = root / name
            if item.exists():
                archive.add(item, arcname=name)
    existing = sorted(paths.BACKUP_DIR.glob("bonbridge-*.tar.gz"))
    for old in existing[:-keep]:
        try:
            old.unlink()
        except OSError:
            pass
    log.info("Backup written to %s", target)
    return target


def list_backups() -> List[Dict[str, Any]]:
    entries = []
    try:
        for path in sorted(paths.BACKUP_DIR.glob("bonbridge-*.tar.gz"), reverse=True):
            stat = path.stat()
            entries.append({"file": path.name, "size": stat.st_size, "time": stat.st_mtime})
    except OSError:
        pass
    return entries


def rollback(backup_file: Optional[str] = None) -> Dict[str, Any]:
    """Restore the most recent backup (or a named one) and reinstall from it."""
    candidates = sorted(paths.BACKUP_DIR.glob("bonbridge-*.tar.gz"), reverse=True)
    if backup_file:
        candidates = [p for p in candidates if p.name == backup_file]
    if not candidates:
        return {"ok": False, "error": "no backup found"}
    chosen = candidates[0]
    work = Path(tempfile.mkdtemp(prefix="bonbridge-rollback-", dir=str(paths.UPDATE_DIR)))
    try:
        source = extract(chosen, work)
    except Exception as exc:  # noqa: BLE001
        shutil.rmtree(work, ignore_errors=True)
        return {"ok": False, "error": f"{chosen.name}: {exc}"}
    return {"ok": True, "backup": chosen.name, "source": str(source), "version": archive_version(source)}


# --------------------------------------------------------------------------
# Running the installer
# --------------------------------------------------------------------------


def systemd_available() -> bool:
    return Path("/run/systemd/system").is_dir() and bool(shutil.which("systemd-run"))


def build_runner_script(source_root: Path, version: str) -> Path:
    """Small shell wrapper so the installer output lands in one log file."""
    script = source_root.parent / "run-update.sh"
    script.write_text(
        "#!/bin/bash\n"
        "# Generated by BonBridge - runs install.sh and records the outcome.\n"
        "set -o pipefail\n"
        f'LOG="{log_file()}"\n'
        f'STATUS="{status_file()}"\n'
        'echo "" >> "$LOG"\n'
        'echo "==================== $(date -Is) ====================" >> "$LOG"\n'
        f'echo "Installing BonBridge {version}" >> "$LOG"\n'
        f'cd "{source_root}" || exit 1\n'
        'bash install.sh >> "$LOG" 2>&1\n'
        "RC=$?\n"
        'if [ "$RC" -eq 0 ]; then\n'
        f'  printf \'{{"running": false, "phase": "done", "ok": true, "version": "{version}"}}\' > "$STATUS"\n'
        '  echo "==> update finished successfully" >> "$LOG"\n'
        "else\n"
        f'  printf \'{{"running": false, "phase": "failed", "ok": false, "version": "{version}", '
        '"error": "install.sh exited with %s"}\' "$RC" > "$STATUS"\n'
        '  echo "==> update FAILED (exit code $RC)" >> "$LOG"\n'
        "fi\n"
        "exit $RC\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return script


def start_detached(source_root: Path, version: str) -> Dict[str, Any]:
    """Run the installer so it survives the restart of the calling daemon."""
    script = build_runner_script(source_root, version)
    write_status(running=True, phase="installing", ok=None, version=version, started_at=time.time())
    append_log(f"==> starting update to {version} from {source_root}")

    if systemd_available():
        unit = f"bonbridge-update-{int(time.time())}"
        command = [
            "systemd-run",
            f"--unit={unit}",
            "--collect",
            "--description=BonBridge update",
            "/bin/bash",
            str(script),
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, timeout=30)  # noqa: S603
            append_log(f"==> running as transient unit {unit}")
            return {"ok": True, "mode": "systemd-run", "unit": unit, "version": version}
        except Exception as exc:  # noqa: BLE001
            append_log(f"!! systemd-run failed ({exc}) - falling back to a background process")
            log.warning("systemd-run failed: %s", exc)

    # No systemd (container, chroot): a detached session is the best we can do.
    try:
        subprocess.Popen(  # noqa: S603
            ["/bin/bash", str(script)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception as exc:  # noqa: BLE001
        write_status(running=False, phase="failed", ok=False, error=str(exc))
        return {"ok": False, "error": str(exc)}
    return {"ok": True, "mode": "background", "version": version}


def run_foreground(source_root: Path, version: str, echo: Any = print) -> int:
    """Run the installer with live output - used by the command line."""
    write_status(running=True, phase="installing", ok=None, version=version, started_at=time.time())
    append_log(f"==> console update to {version} from {source_root}")
    process = subprocess.Popen(  # noqa: S603
        ["bash", "install.sh"],
        cwd=str(source_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None
    for line in process.stdout:
        echo(line.rstrip())
        append_log(line.rstrip())
    code = process.wait()
    write_status(
        running=False,
        phase="done" if code == 0 else "failed",
        ok=code == 0,
        version=version,
        error="" if code == 0 else f"install.sh exited with {code}",
    )
    return code


# --------------------------------------------------------------------------
# The pieces the daemon and the CLI both use
# --------------------------------------------------------------------------


def prepare_from_release(info: Dict[str, Any], echo: Any = log.info) -> Path:
    """Download and unpack the release described by :func:`check`."""
    tag = str(info.get("tag") or "")
    repository = str(info.get("repository") or "loe17/Bonbridge")
    url = info.get("tarball_url") or (
        f"https://codeload.github.com/{repository}/tar.gz/refs/tags/{tag}"
    )
    paths.UPDATE_DIR.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="bonbridge-update-", dir=str(paths.UPDATE_DIR)))
    archive = work / "release.tar.gz"
    echo(f"Downloading {url}")
    download(url, archive)
    echo(f"Unpacking {archive.name} ({archive.stat().st_size} bytes)")
    source = extract(archive, work / "src")
    found = archive_version(source)
    expected = str(info.get("latest") or "")
    if expected and found and parse_version(found) != parse_version(expected):
        raise ValueError(
            f"the archive contains version {found}, but {expected} was expected"
        )
    return source


def prepare_from_file(archive_path: Path, echo: Any = log.info) -> Path:
    paths.UPDATE_DIR.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="bonbridge-offline-", dir=str(paths.UPDATE_DIR)))
    echo(f"Unpacking {archive_path.name}")
    return extract(archive_path, work / "src")


def cleanup_work_dirs(keep_newest: int = 2) -> None:
    """Old unpacked update trees add up on a small SD card."""
    try:
        directories = sorted(
            (p for p in paths.UPDATE_DIR.iterdir() if p.is_dir()),
            key=lambda p: p.stat().st_mtime,
        )
    except OSError:
        return
    for old in directories[: max(0, len(directories) - keep_newest)]:
        shutil.rmtree(old, ignore_errors=True)


class UpdateChecker(threading.Thread):
    """Checks GitHub once at start-up and then every ``interval`` hours."""

    def __init__(self, repository: str, interval_hours: float = 24.0):
        super().__init__(name="update-check", daemon=True)
        self.repository = repository
        self.interval = max(1.0, float(interval_hours)) * 3600.0
        self.result: Dict[str, Any] = {}
        self._stop_event = threading.Event()

    def check_now(self) -> Dict[str, Any]:
        self.result = check(self.repository)
        if self.result.get("update_available"):
            log.info(
                "Update available: %s (installed: %s)",
                self.result.get("latest"),
                __version__,
            )
        return self.result

    def run(self) -> None:
        # A moment after start-up, so it never delays the first print job.
        if self._stop_event.wait(20.0):
            return
        while not self._stop_event.is_set():
            try:
                self.check_now()
            except Exception as exc:  # noqa: BLE001
                log.debug("update check failed: %s", exc)
            if self._stop_event.wait(self.interval):
                return

    def stop(self) -> None:
        self._stop_event.set()
