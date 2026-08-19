"""Print job queue and the per-printer worker thread.

One :class:`PrinterWorker` owns exactly one transport.  Everything that wants
to print - the RAW listener on port 9100, the web interface's test prints,
the optional CUPS backend - hands a :class:`Job` to the worker.  Because the
worker is the only writer, jobs can never interleave, and a failed job can be
spooled and retried instead of silently disappearing (which is what happened
with the old ``socat`` bridge).
"""

from __future__ import annotations

import itertools
import logging
import queue
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from . import caps, escpos, paths, state
from .transports import TransportError, build_transport
from .transports.base import BaseTransport

log = logging.getLogger(__name__)

_job_counter = itertools.count(1)


@dataclass
class Job:
    """A chunk of raw printer data waiting to be delivered."""

    data: bytes
    source: str = "internal"
    printer_id: str = ""
    job_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    number: int = field(default_factory=lambda: next(_job_counter))
    created: float = field(default_factory=time.time)
    attempts: int = 0
    spool_path: Optional[Path] = None
    response_sink: Optional[Callable[[bytes], None]] = None
    label: str = ""

    @property
    def size(self) -> int:
        return len(self.data)

    def summary(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "number": self.number,
            "source": self.source,
            "size": self.size,
            "created": self.created,
            "attempts": self.attempts,
            "label": self.label,
            "spooled": self.spool_path is not None,
        }


class PrinterWorker(threading.Thread):
    """Serialises all access to one physical printer."""

    def __init__(self, printer_config: Dict[str, Any]):
        super().__init__(name=f"printer-{printer_config.get('id', '?')}", daemon=True)
        self.config = printer_config
        self.printer_id: str = printer_config["id"]
        self.queue: "queue.Queue[Optional[Job]]" = queue.Queue()
        self.transport: Optional[BaseTransport] = None

        self._stop_event = threading.Event()
        self._state_lock = threading.RLock()
        self._connect_lock = threading.RLock()

        self.connected = False
        self.last_error: Optional[str] = None
        self.last_error_at: Optional[float] = None
        self.last_job_at: Optional[float] = None
        self.jobs_total = 0
        self.jobs_failed = 0
        self.bytes_total = 0
        self.started_at = time.time()
        self.status: Dict[str, Any] = {}
        self.status_level = "unknown"
        self.status_messages: List[str] = []
        self.status_checked_at: Optional[float] = None
        self.identity: Dict[str, Any] = {}
        self.capabilities: Dict[str, Any] = {}
        self.recent_jobs: List[Dict[str, Any]] = []
        self._last_status_attempt = 0.0
        self._reconnect_delay = 1.0

        # Cash drawer: the pin can only prove "connected" when it reads LOW, so
        # remember that fact across restarts (see caps.drawer_state).
        self.drawer: Dict[str, Any] = caps.drawer_state({})
        self._drawer_seen = bool(state.get("drawer_seen", self.printer_id, False))
        # Paper-low warning: printed once per "roll", reset when paper is OK
        # again.  Persisted so a reboot does not reprint it.
        self._paper_low_reported = bool(state.get("paper_low_reported", self.printer_id, False))
        self._startup_report_done = False
        #: Filled in by the daemon so the startup slip can name the IP address.
        self.report_context: Dict[str, Any] = {}

        self.spool_dir = paths.SPOOL_DIR / self.printer_id

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------

    @property
    def options(self) -> Dict[str, Any]:
        return self.config.get("options") or {}

    @property
    def queue_options(self) -> Dict[str, Any]:
        return self.config.get("queue") or {}

    @property
    def enabled(self) -> bool:
        return bool(self.config.get("enabled", True))

    # ------------------------------------------------------------------
    # Connection handling
    # ------------------------------------------------------------------

    def _ensure_transport(self) -> BaseTransport:
        with self._connect_lock:
            if self.transport is not None and self.transport.is_open:
                return self.transport
            if self.transport is None:
                self.transport = build_transport(self.config.get("transport"))
            self.transport.open()
            self.connected = True
            self.last_error = None
            self._reconnect_delay = 1.0
            log.info("[%s] connected via %s", self.printer_id, self.transport.connection_label())
            self._identify()
            return self.transport

    def _drop_transport(self, reason: str) -> None:
        with self._connect_lock:
            self.connected = False
            self.last_error = reason
            self.last_error_at = time.time()
            if self.transport is not None:
                try:
                    self.transport.close()
                except Exception:  # noqa: BLE001
                    pass
            # Rebuild from scratch next time so that a replugged device with a
            # new bus address is picked up.
            self.transport = None

    @staticmethod
    def _as_int(value: Any) -> Optional[int]:
        if value is None or value == "":
            return None
        if isinstance(value, int):
            return value
        text = str(value).strip().lower()
        try:
            return int(text, 16) if text.startswith("0x") else int(text, 0)
        except ValueError:
            return None

    def _find_scanned_device(self, settings: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find the freshly scanned device entry matching our transport."""
        from .transports import scan_devices

        want_vendor = self._as_int(settings.get("vendor_id"))
        want_product = self._as_int(settings.get("product_id"))
        want_device = settings.get("device")

        for device in scan_devices():
            if want_device and device.get("device") == want_device:
                return device
            if want_vendor is not None and device.get("vendor_id") == want_vendor:
                if want_product is None or device.get("product_id") == want_product:
                    return device
        return None

    def _identify(self) -> None:
        """Read printer identity and build the capability object."""
        transport = self.transport
        if transport is None:
            return
        try:
            identity = caps.query_identity(transport)
        except Exception as exc:  # noqa: BLE001
            log.debug("[%s] identity query failed: %s", self.printer_id, exc)
            identity = {"gs_i": {}, "readable": False}

        settings = dict(getattr(transport, "settings", {}) or {})
        identity.setdefault("product", settings.get("product") or "")
        identity.setdefault("manufacturer", settings.get("manufacturer") or "")
        identity.setdefault("vendor_id", settings.get("vendor_id"))
        identity.setdefault("product_id", settings.get("product_id"))
        identity["connection"] = transport.connection_label()
        identity["transport"] = transport.type_name

        # Enrich from a fresh device scan so USB descriptor strings are
        # available even when the transport itself did not read them.
        try:
            match = self._find_scanned_device(settings)
            if match:
                identity["product"] = identity.get("product") or match.get("product", "")
                identity["manufacturer"] = identity.get("manufacturer") or match.get(
                    "manufacturer", ""
                )
                identity["serial"] = identity.get("serial") or match.get("serial", "")
                if match.get("ieee1284_id"):
                    identity["ieee1284_id"] = match["ieee1284_id"]
                identity.setdefault("vendor_id", match.get("vendor_id"))
                identity.setdefault("product_id", match.get("product_id"))
        except Exception as exc:  # noqa: BLE001
            log.debug("[%s] device enrichment failed: %s", self.printer_id, exc)

        configured = str(self.config.get("profile") or "auto")
        if configured and configured != "auto":
            profile_id, reason = configured, "manuell gewählt / manually selected"
        else:
            profile_id, reason = caps.match_profile(identity)
        identity["profile_reason"] = reason

        self.identity = identity
        self.capabilities = caps.build_capabilities(
            profile_id,
            identity=identity,
            overrides=self.config.get("features") or {},
            status_readback=bool(transport.bidirectional and identity.get("readable")),
        )
        log.info(
            "[%s] identified as profile '%s' (%s)",
            self.printer_id,
            profile_id,
            reason,
        )
        self._maybe_startup_report()

    # ------------------------------------------------------------------
    # Automatic slips
    # ------------------------------------------------------------------

    def _maybe_startup_report(self) -> None:
        """Print the "here is my IP address" slip, once per daemon start."""
        if self._startup_report_done:
            return
        self._startup_report_done = True
        if not self.options.get("startup_report", True):
            log.info("[%s] startup report disabled", self.printer_id)
            return
        builder = self.report_context.get("build_startup_report")
        if not callable(builder):
            return
        try:
            payload = builder(self)
        except Exception as exc:  # noqa: BLE001 - never block start-up
            log.warning("[%s] cannot build the startup report: %s", self.printer_id, exc)
            return
        if payload:
            self.submit_bytes(payload, source="startup", label="startup-report")
            log.info("[%s] startup report queued", self.printer_id)

    def _maybe_paper_low(self) -> None:
        """Print a warning slip when the roll starts running out."""
        paper = (self.status or {}).get("paper") or {}
        near_end = bool(paper.get("paper_near_end")) or bool(paper.get("paper_end"))

        if not near_end:
            if self._paper_low_reported:
                self._paper_low_reported = False
                state.set_value("paper_low_reported", self.printer_id, False)
                log.info("[%s] paper level back to normal", self.printer_id)
            return

        if self._paper_low_reported or not self.options.get("paper_low_warning", False):
            return

        capabilities = self.capabilities or {}
        recommendation = capabilities.get("recommendation") or {}
        features = capabilities.get("features") or {}
        payload = escpos.paper_low_page(
            printer_name=str(self.config.get("name") or self.printer_id),
            columns=int(recommendation.get("columns") or 42),
            codepage=str(recommendation.get("codepage") or "cp1252"),
            language=str(self.report_context.get("language") or "de"),
            timestamp=time.strftime("%Y-%m-%d %H:%M"),
            do_cut=bool((features.get("cutter") or {}).get("effective", True)),
        )
        self.submit_bytes(payload, source="paper-low", label="paper-low-warning")
        self._paper_low_reported = True
        state.set_value("paper_low_reported", self.printer_id, True)
        log.info("[%s] paper low - warning slip queued", self.printer_id)

    def note_drawer_seen(self) -> None:
        """Remember that a cash drawer proved to be connected."""
        if not self._drawer_seen:
            self._drawer_seen = True
            state.set_value("drawer_seen", self.printer_id, True)
            log.info("[%s] cash drawer detected as connected", self.printer_id)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def submit(self, job: Job) -> Job:
        job.printer_id = self.printer_id
        self.queue.put(job)
        return job

    def submit_bytes(
        self,
        data: bytes,
        source: str = "internal",
        label: str = "",
        response_sink: Optional[Callable[[bytes], None]] = None,
    ) -> Job:
        return self.submit(Job(data=data, source=source, label=label, response_sink=response_sink))

    def stop(self) -> None:
        self._stop_event.set()
        self.queue.put(None)

    def pending(self) -> int:
        return self.queue.qsize()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:  # noqa: C901 - the loop is intentionally explicit
        log.info("[%s] worker started", self.printer_id)
        self._load_spool()
        while not self._stop_event.is_set():
            try:
                job = self.queue.get(timeout=1.0)
            except queue.Empty:
                self._idle_tick()
                continue
            if job is None:
                break
            try:
                self._process(job)
            except Exception as exc:  # noqa: BLE001 - never kill the worker
                log.exception("[%s] unexpected error while printing: %s", self.printer_id, exc)
            finally:
                self.queue.task_done()
        self._drop_transport("worker stopped")
        log.info("[%s] worker stopped", self.printer_id)

    def _idle_tick(self) -> None:
        """Runs roughly once a second while no job is queued."""
        if not self.enabled:
            return
        if not self.connected:
            # Backoff reconnect so a missing printer does not spam the log.
            if time.monotonic() - self._last_status_attempt < self._reconnect_delay:
                return
            self._last_status_attempt = time.monotonic()
            try:
                self._ensure_transport()
            except TransportError as exc:
                self._reconnect_delay = min(self._reconnect_delay * 2, 30.0)
                if self.last_error != str(exc):
                    log.warning("[%s] not connected: %s", self.printer_id, exc)
                self._drop_transport(str(exc))
                return
            except Exception as exc:  # noqa: BLE001
                self._reconnect_delay = min(self._reconnect_delay * 2, 30.0)
                self._drop_transport(str(exc))
                return

        if not self.options.get("status_polling", True):
            return
        interval = float(self.options.get("status_interval") or 10.0)
        if self.status_checked_at and time.time() - self.status_checked_at < interval:
            return
        self.refresh_status()

    def refresh_status(self) -> Dict[str, Any]:
        """Query DLE EOT status; safe to call from the web interface."""
        with self._state_lock:
            transport = self.transport
            if transport is None or not transport.is_open:
                self.status = {}
                self.status_level = "offline" if not self.connected else "unknown"
                self.status_messages = [self.last_error or "not connected"]
                self.status_checked_at = time.time()
                return self.status
            try:
                status = caps.read_status(transport)
            except TransportError as exc:
                self._drop_transport(str(exc))
                self.status = {}
                self.status_level = "offline"
                self.status_messages = [str(exc)]
                self.status_checked_at = time.time()
                return self.status
            self.status = status
            self.status_level, self.status_messages = escpos.summarise_status(status)
            self.status_checked_at = time.time()

            printer_status = status.get("printer") or {}
            if printer_status.get("drawer_pin_high") is False:
                self.note_drawer_seen()
            self.drawer = caps.drawer_state(status, seen_connected=self._drawer_seen)

            self._maybe_paper_low()
            return status

    # ------------------------------------------------------------------
    # Job processing
    # ------------------------------------------------------------------

    def _postamble(self) -> bytes:
        """Optional bytes appended after each job (feed / cut / drawer)."""
        options = self.options
        features = (self.capabilities or {}).get("features") or {}

        def feature_on(name: str) -> bool:
            entry = features.get(name) or {}
            return bool(entry.get("effective", True))

        out = bytearray()
        lines = int(options.get("feed_lines_after_job") or 0)
        if lines:
            out += escpos.feed(lines)
        if options.get("cut_after_job") and feature_on("cutter"):
            out += escpos.cut(str(options.get("cut_mode") or "partial"))
        if options.get("open_drawer_after_job") and feature_on("cashdrawer"):
            out += escpos.drawer_pulse(int(options.get("drawer_pin") or 0))
        return bytes(out)

    def _preamble(self) -> bytes:
        options = self.options
        out = bytearray()
        if options.get("reset_before_job"):
            out += escpos.INIT
        forced = options.get("force_codepage")
        if forced:
            out += escpos.select_codepage(str(forced))
        return bytes(out)

    def _process(self, job: Job) -> None:
        max_retries = int(self.queue_options.get("max_retries") or 0)
        retry_seconds = float(self.queue_options.get("retry_seconds") or 5.0)

        while not self._stop_event.is_set():
            job.attempts += 1
            try:
                transport = self._ensure_transport()
                payload = self._preamble() + job.data + self._postamble()
                transport.write(payload)
                self._after_success(job, transport)
                return
            except TransportError as exc:
                self._drop_transport(str(exc))
                self.jobs_failed += 1
                log.warning(
                    "[%s] job %s attempt %s failed: %s",
                    self.printer_id,
                    job.number,
                    job.attempts,
                    exc,
                )
            except Exception as exc:  # noqa: BLE001
                self._drop_transport(str(exc))
                self.jobs_failed += 1
                log.exception("[%s] job %s failed: %s", self.printer_id, job.number, exc)

            if max_retries and job.attempts >= max_retries:
                log.error(
                    "[%s] giving up on job %s after %s attempts", self.printer_id, job.number, job.attempts
                )
                if self.queue_options.get("spool_on_error", True):
                    self._spool(job)
                return

            if self.queue_options.get("spool_on_error", True) and job.spool_path is None:
                self._spool(job)

            # Wait before retrying, but stay responsive to shutdown.
            waited = 0.0
            while waited < retry_seconds and not self._stop_event.is_set():
                time.sleep(0.2)
                waited += 0.2

    def _after_success(self, job: Job, transport: BaseTransport) -> None:
        self.jobs_total += 1
        self.bytes_total += job.size
        self.last_job_at = time.time()
        self.last_error = None
        log.info(
            "[%s] job %s printed (%s bytes, source %s)",
            self.printer_id,
            job.number,
            job.size,
            job.source,
        )
        self._remember(job)
        self._unspool(job)

        # Forward anything the printer sends back to the originating socket -
        # this is what a real JetDirect interface does and what POS software
        # expects when it asks for status over the same connection.
        if job.response_sink is not None and transport.bidirectional:
            try:
                reply = transport.read(256, 0.3)
                if reply:
                    job.response_sink(reply)
            except Exception as exc:  # noqa: BLE001
                log.debug("[%s] status passthrough failed: %s", self.printer_id, exc)

    def _remember(self, job: Job) -> None:
        entry = job.summary()
        entry["printed_at"] = time.time()
        entry["preview"] = _preview(job.data)
        self.recent_jobs.insert(0, entry)
        keep = 20
        del self.recent_jobs[keep:]

    # ------------------------------------------------------------------
    # Spooling
    # ------------------------------------------------------------------

    def _spool(self, job: Job) -> None:
        try:
            self.spool_dir.mkdir(parents=True, exist_ok=True)
            path = self.spool_dir / f"{int(job.created)}-{job.job_id}.bin"
            path.write_bytes(job.data)
            job.spool_path = path
            log.info("[%s] job %s spooled to %s", self.printer_id, job.number, path)
            self._trim_spool()
        except OSError as exc:
            log.error("[%s] cannot spool job %s: %s", self.printer_id, job.number, exc)

    def _unspool(self, job: Job) -> None:
        if job.spool_path is None:
            return
        try:
            job.spool_path.unlink()
        except OSError:
            pass
        job.spool_path = None

    def _trim_spool(self) -> None:
        limit = int(self.queue_options.get("max_spool_files") or 200)
        try:
            files = sorted(self.spool_dir.glob("*.bin"))
        except OSError:
            return
        for path in files[:-limit] if len(files) > limit else []:
            try:
                path.unlink()
            except OSError:
                pass

    def _load_spool(self) -> None:
        """Re-queue jobs that were not delivered before the last shutdown."""
        try:
            files = sorted(self.spool_dir.glob("*.bin"))
        except OSError:
            return
        for path in files:
            try:
                data = path.read_bytes()
            except OSError:
                continue
            if not data:
                try:
                    path.unlink()
                except OSError:
                    pass
                continue
            job = Job(data=data, source="spool", label=path.name)
            job.spool_path = path
            self.submit(job)
        if files:
            log.info("[%s] re-queued %s spooled job(s)", self.printer_id, len(files))

    def spool_count(self) -> int:
        try:
            return len(list(self.spool_dir.glob("*.bin")))
        except OSError:
            return 0

    def clear_spool(self) -> int:
        removed = 0
        try:
            for path in self.spool_dir.glob("*.bin"):
                try:
                    path.unlink()
                    removed += 1
                except OSError:
                    pass
        except OSError:
            pass
        return removed

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        transport = self.transport
        return {
            "id": self.printer_id,
            "name": self.config.get("name") or self.printer_id,
            "enabled": self.enabled,
            "connected": self.connected,
            "bind": self.config.get("bind") or "0.0.0.0",
            "transport": (
                transport.describe()
                if transport
                else {"type": (self.config.get("transport") or {}).get("type", "auto")}
            ),
            "connection": transport.connection_label() if transport else "",
            "status_level": self.status_level,
            "status_messages": self.status_messages,
            "status": self.status,
            "status_checked_at": self.status_checked_at,
            "last_error": self.last_error,
            "last_error_at": self.last_error_at,
            "last_job_at": self.last_job_at,
            "jobs_total": self.jobs_total,
            "jobs_failed": self.jobs_failed,
            "bytes_total": self.bytes_total,
            "queued": self.pending(),
            "spooled": self.spool_count(),
            "identity": self.identity,
            "drawer": self.drawer,
            "capabilities": self.capabilities,
            "recent_jobs": self.recent_jobs,
            "uptime": time.time() - self.started_at,
        }


def _preview(data: bytes, limit: int = 160) -> str:
    """Printable preview of a job for the diagnostics page."""
    text = data.decode("cp437", "replace")
    cleaned = "".join(ch if 32 <= ord(ch) < 127 or ch in "\n\t" else "." for ch in text)
    cleaned = cleaned.replace("\n", " | ")
    return cleaned[:limit]
