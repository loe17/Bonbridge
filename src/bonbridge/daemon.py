"""The BonBridge daemon: wires printers, RAW listeners and the web interface."""

from __future__ import annotations

import logging
import re
import shutil
import signal
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from . import (
    __version__,
    caps,
    discovery,
    escpos,
    health,
    images,
    mdns,
    netwatch,
    paths,
    receipts,
    sysinfo,
    updater,
)
from .config import Config
from .jobs import Job, PrinterWorker
from .raw_server import RawListenerSupervisor
from .transports import runtime_report, scan_devices

log = logging.getLogger(__name__)


class PrinterRuntime:
    """A printer's worker plus its RAW listener."""

    def __init__(self, printer_config: Dict[str, Any], raw_port: int, max_connections: int):
        self.config = printer_config
        self.worker = PrinterWorker(printer_config)
        self.listener: Optional[RawListenerSupervisor] = None
        self.raw_port = raw_port
        self.max_connections = max_connections

    @property
    def printer_id(self) -> str:
        return self.config["id"]

    def start(self) -> None:
        self.worker.start()
        if not self.config.get("enabled", True):
            log.info("[%s] disabled - no RAW listener started", self.printer_id)
            return
        self.listener = RawListenerSupervisor(
            self.printer_id,
            str(self.config.get("bind") or "0.0.0.0"),
            self.raw_port,
            self._deliver,
            max_connections=self.max_connections,
        )
        self.listener.start()

    def _deliver(self, data: bytes, peer: str, send_back: Callable[[bytes], None]) -> None:
        self.worker.submit(
            Job(data=data, source=peer, label=f"RAW {len(data)} B", response_sink=send_back)
        )

    def stop(self) -> None:
        if self.listener is not None:
            self.listener.stop()
        self.worker.stop()

    def snapshot(self) -> Dict[str, Any]:
        data = self.worker.snapshot()
        data["listener"] = (
            self.listener.snapshot()
            if self.listener is not None
            else {"listening": False, "bind": self.config.get("bind"), "port": self.raw_port}
        )
        return data


class BonBridge:
    """Top level application object.  The web layer talks to this."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.load()
        self.printers: Dict[str, PrinterRuntime] = {}
        self.started_at = time.time()
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self.mdns = mdns.MdnsAdvertiser()
        self.enpc: Optional[discovery.EnpcResponder] = None
        self.netwatch: Optional[netwatch.NetworkWatcher] = None
        self.update_checker: Optional[updater.UpdateChecker] = None
        self.web_server: Any = None
        self.version = __version__
        #: Rasterised images waiting to be printed, keyed by preview token.
        self._image_cache: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        paths.ensure_runtime_dirs()
        self._ensure_default_printer()
        self._start_printers()
        self._start_discovery()
        self._start_netwatch()
        self._start_update_checker()
        log.info("BonBridge %s ready with %s printer(s)", self.version, len(self.printers))

    def _ensure_default_printer(self) -> None:
        """First start: create a printer entry for whatever is plugged in."""
        if self.config.printers:
            return
        from .transports import autodetect_settings

        detected = autodetect_settings()
        entry: Dict[str, Any] = {
            "id": "printer1",
            "name": "Drucker 1",
            "enabled": True,
            "bind": "0.0.0.0",
            "transport": detected or {"type": "auto"},
            "profile": "auto",
        }
        self.config.add_printer(entry)
        try:
            self.config.save()
        except OSError as exc:
            log.warning("Cannot write initial configuration: %s", exc)
        log.info(
            "Created initial printer entry (%s)",
            "auto-detected" if detected else "no device found yet",
        )

    def _start_printers(self) -> None:
        raw_port = int((self.config.data.get("raw") or {}).get("port") or 9100)
        max_connections = int((self.config.data.get("raw") or {}).get("max_connections") or 8)
        language = str((self.config.data.get("web") or {}).get("language") or "de")
        for printer_config in self.config.printers:
            runtime = PrinterRuntime(printer_config, raw_port, max_connections)
            runtime.worker.report_context = {
                "language": language,
                "build_startup_report": self.build_startup_report,
            }
            self.printers[runtime.printer_id] = runtime
            runtime.start()

    def _start_discovery(self) -> None:
        settings = self.config.data.get("discovery") or {}
        web_port = int((self.config.data.get("web") or {}).get("port") or 8080)
        raw_port = int((self.config.data.get("raw") or {}).get("port") or 9100)
        announced = []
        for runtime in self.printers.values():
            if not runtime.config.get("enabled", True):
                continue
            capabilities = runtime.worker.capabilities or {}
            announced.append(
                {
                    "id": runtime.printer_id,
                    "name": runtime.config.get("name"),
                    "port": raw_port,
                    "model": capabilities.get("profile_name") or "ESC-POS",
                    "vendor": capabilities.get("vendor") or "BonBridge",
                }
            )
        if settings.get("mdns", True):
            mdns.write_avahi_service_file(
                announced, web_port, str(self.config.data.get("hostname_label") or "")
            )
            self.mdns.start(announced, web_port)
        if settings.get("enpc", True):
            self.enpc = discovery.EnpcResponder(
                device_name_provider=lambda: str(
                    self.config.data.get("hostname_label") or sysinfo.hostname()
                ),
                mac_provider=discovery.local_mac,
                ip_provider=sysinfo.primary_ipv4,
                log_probes=bool(settings.get("log_probes", True)),
                port=int(settings.get("enpc_port") or discovery.ENPC_PORT),
            )
            self.enpc.start()

    # ------------------------------------------------------------------
    # Network watchdog
    # ------------------------------------------------------------------

    def _start_netwatch(self) -> None:
        settings = self.config.data.get("network_watch") or {}
        if not settings.get("enabled", True):
            log.info("Network watchdog disabled")
            return
        self.netwatch = netwatch.NetworkWatcher(
            self._on_network_change,
            interval=float(settings.get("interval") or 60.0),
            gateway_check=bool(settings.get("gateway_check", False)),
            confirmations=int(settings.get("confirmations") or 2),
        )
        self.netwatch.start()

    def _on_network_change(
        self, online: bool, state: Dict[str, Any], offline_since: Optional[float]
    ) -> None:
        """Print the outage / recovery slip on every printer that wants it."""
        settings = self.config.data.get("network_watch") or {}
        if online and not settings.get("print_on_restore", True):
            return
        if not online and not settings.get("print_on_loss", True):
            return

        language = str((self.config.data.get("web") or {}).get("language") or "de")
        german = language.lower().startswith("de")
        outage = ""
        if online and offline_since:
            minutes = max(1, int((time.time() - offline_since) // 60))
            outage = f"{minutes} min"

        for runtime in list(self.printers.values()):
            worker = runtime.worker
            if not (runtime.config.get("options") or {}).get("network_alert", True):
                continue
            # "No printer attached" must stay silent: a spooled outage slip
            # would surface days later out of context.
            if not worker.connected:
                log.info(
                    "[%s] network %s - not printing, printer is not connected",
                    runtime.printer_id,
                    "restored" if online else "lost",
                )
                continue
            capabilities = worker.capabilities or {}
            recommendation = capabilities.get("recommendation") or {}
            features = capabilities.get("features") or {}
            payload = escpos.network_alert_page(
                online=online,
                printer_name=str(runtime.config.get("name") or runtime.printer_id),
                reason=str(state.get("reason_de" if german else "reason_en") or ""),
                columns=int(recommendation.get("columns") or 42),
                codepage=str(recommendation.get("codepage") or "cp1252"),
                language=language,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                rows=netwatch.describe_links(state, german),
                outage=outage,
                address=str(state.get("ip") or "") if online else "",
                do_cut=bool((features.get("cutter") or {}).get("effective", True)),
            )
            worker.submit_bytes(
                payload,
                source="netwatch",
                label="network-online" if online else "network-offline",
            )

    def network_state(self) -> Dict[str, Any]:
        settings = self.config.data.get("network_watch") or {}
        if self.netwatch is None:
            return {"enabled": False, "online": None, "interfaces": [], **dict(settings)}
        return self.netwatch.snapshot_dict()

    def check_network(self) -> Dict[str, Any]:
        """Run one check on demand (button in the web interface)."""
        if self.netwatch is None:
            return {"ok": False, "error": "network watchdog is disabled"}
        self.netwatch.check_once()
        return {"ok": True, "network": self.netwatch.snapshot_dict()}

    def test_network_alert(self, printer_id: str, online: bool = False) -> Dict[str, Any]:
        """Print the outage slip on demand so its wording can be checked."""
        runtime = self.printers.get(printer_id)
        if runtime is None:
            return {"ok": False, "error": f"unknown printer '{printer_id}'"}
        state = self.network_state()
        if not state.get("interfaces"):
            state = netwatch.snapshot(False)
        language = str((self.config.data.get("web") or {}).get("language") or "de")
        german = language.lower().startswith("de")
        capabilities = runtime.worker.capabilities or {}
        recommendation = capabilities.get("recommendation") or {}
        features = capabilities.get("features") or {}
        payload = escpos.network_alert_page(
            online=online,
            printer_name=str(runtime.config.get("name") or printer_id),
            reason=str(state.get("reason_de" if german else "reason_en") or ""),
            columns=int(recommendation.get("columns") or 42),
            codepage=str(recommendation.get("codepage") or "cp1252"),
            language=language,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            rows=netwatch.describe_links(state, german),
            address=str(state.get("ip") or "") if online else "",
            do_cut=bool((features.get("cutter") or {}).get("effective", True)),
        )
        runtime.worker.submit_bytes(payload, source="web-ui", label="network-test")
        return {"ok": True, "queued": True, "bytes": len(payload)}

    # ------------------------------------------------------------------
    # Software updates
    # ------------------------------------------------------------------

    @property
    def update_settings(self) -> Dict[str, Any]:
        return self.config.data.get("update") or {}

    def _start_update_checker(self) -> None:
        settings = self.update_settings
        if not settings.get("check_on_start", True):
            return
        self.update_checker = updater.UpdateChecker(
            str(settings.get("repository") or "loe17/Bonbridge"),
            float(settings.get("check_interval_hours") or 24.0),
        )
        self.update_checker.start()

    def update_state(self) -> Dict[str, Any]:
        """What the web interface needs to show about updates."""
        settings = self.update_settings
        status = updater.read_status()
        latest = dict(self.update_checker.result) if self.update_checker else {}
        return {
            "current": self.version,
            "repository": str(settings.get("repository") or "loe17/Bonbridge"),
            "allow_web": bool(settings.get("allow_web", True)),
            "check_on_start": bool(settings.get("check_on_start", True)),
            "latest": latest.get("latest") or "",
            "update_available": bool(latest.get("update_available")),
            "checked_at": latest.get("checked_at"),
            "check_error": latest.get("error") or "",
            "release": {
                "name": latest.get("name") or "",
                "notes": latest.get("notes") or "",
                "html_url": latest.get("html_url") or "",
                "published_at": latest.get("published_at") or "",
            },
            "status": status,
            "backups": updater.list_backups(),
            "systemd": updater.systemd_available(),
        }

    def check_update(self) -> Dict[str, Any]:
        settings = self.update_settings
        repository = str(settings.get("repository") or "loe17/Bonbridge")
        if self.update_checker is None:
            self.update_checker = updater.UpdateChecker(
                repository, float(settings.get("check_interval_hours") or 24.0)
            )
        result = self.update_checker.check_now()
        return {"ok": bool(result.get("ok")), "check": result, "update": self.update_state()}

    def _require_web_updates(self) -> None:
        if not self.update_settings.get("allow_web", True):
            raise PermissionError(
                "Updates ueber die Weboberflaeche sind abgeschaltet "
                "(System -> Updates). Auf der Konsole: sudo bonbridge update"
            )

    def start_update(self, source: str = "online", filename: str = "") -> Dict[str, Any]:
        """Kick off an installation in the background.  Web interface entry."""
        self._require_web_updates()
        status = updater.read_status()
        if status.get("running"):
            return {"ok": False, "error": "an update is already running"}
        try:
            if source == "file":
                archive = paths.UPDATE_DIR / "uploads" / filename
                if not archive.is_file():
                    return {"ok": False, "error": f"no uploaded file '{filename}'"}
                root = updater.prepare_from_file(archive)
            else:
                info = (self.update_checker.result if self.update_checker else {}) or {}
                if not info.get("tag"):
                    info = updater.check(str(self.update_settings.get("repository") or ""))
                if not info.get("ok"):
                    return {"ok": False, "error": info.get("error") or "no release found"}
                root = updater.prepare_from_release(info)
            version = updater.archive_version(root) or "?"
        except Exception as exc:  # noqa: BLE001 - reported to the user verbatim
            log.warning("Update preparation failed: %s", exc)
            updater.write_status(running=False, phase="failed", ok=False, error=str(exc))
            return {"ok": False, "error": str(exc)}
        # Back up before touching anything.  An update that breaks the bridge
        # during service has to be undoable with one command.
        saved = None
        try:
            saved = updater.backup()
            if saved:
                updater.append_log(f"==> backup written to {saved}")
        except Exception as exc:  # noqa: BLE001 - never block the update on this
            log.warning("Backup before the update failed: %s", exc)
            updater.append_log(f"!! backup failed: {exc}")
        updater.cleanup_work_dirs()
        result = updater.start_detached(root, version)
        result["source"] = source
        result["backup"] = str(saved) if saved else ""
        return result

    def store_upload(self, filename: str, data: bytes) -> Dict[str, Any]:
        """Accept an uploaded release archive and check that it is one."""
        self._require_web_updates()
        if len(data) > updater.MAX_ARCHIVE_BYTES:
            return {"ok": False, "error": "file is too large"}
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", filename or "upload.tar.gz")[:80]
        target_dir = paths.UPDATE_DIR / "uploads"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / safe
        target.write_bytes(data)
        # Unpack once immediately: an unusable file should be rejected while
        # the user is still looking at the upload dialog, not later.
        probe = Path(tempfile.mkdtemp(prefix="bonbridge-probe-", dir=str(paths.UPDATE_DIR)))
        try:
            root = updater.extract(target, probe)
            version = updater.archive_version(root)
        except Exception as exc:  # noqa: BLE001
            try:
                target.unlink()
            except OSError:
                pass
            return {"ok": False, "error": str(exc)}
        finally:
            shutil.rmtree(probe, ignore_errors=True)
        return {
            "ok": True,
            "file": safe,
            "bytes": len(data),
            "version": version,
            "newer": updater.is_newer(version, self.version),
        }

    def update_log(self, lines: int = 200) -> Dict[str, Any]:
        return {
            "ok": True,
            "status": updater.read_status(),
            "log": updater.tail_log(lines),
            "version": self.version,
        }

    def stop(self) -> None:
        log.info("Shutting down")
        self._stop_event.set()
        if self.netwatch is not None:
            self.netwatch.stop()
            self.netwatch = None
        if self.update_checker is not None:
            self.update_checker.stop()
            self.update_checker = None
        with self._lock:
            for runtime in self.printers.values():
                runtime.stop()
            self.printers.clear()
        if self.enpc is not None:
            self.enpc.stop()
            self.enpc = None
        self.mdns.stop()

    def wait(self) -> None:
        while not self._stop_event.is_set():
            time.sleep(0.5)

    def install_signal_handlers(self) -> None:
        def handler(signum: int, _frame: Any) -> None:
            log.info("Received signal %s", signum)
            self._stop_event.set()

        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                signal.signal(sig, handler)
            except (ValueError, OSError):  # not on the main thread
                pass

    def restart_printers(self) -> None:
        """Apply configuration changes without restarting the process."""
        with self._lock:
            for runtime in self.printers.values():
                runtime.stop()
            # Give listeners a moment to release their sockets.
            time.sleep(0.4)
            self.printers.clear()
            self._start_printers()
        log.info("Printers restarted (%s active)", len(self.printers))

    # ------------------------------------------------------------------
    # Queries used by the web interface
    # ------------------------------------------------------------------

    def runtime(self, printer_id: str) -> Optional[PrinterRuntime]:
        return self.printers.get(printer_id)

    def overview(self) -> Dict[str, Any]:
        raw_port = int((self.config.data.get("raw") or {}).get("port") or 9100)
        ip = sysinfo.primary_ipv4()
        printers = [runtime.snapshot() for runtime in self.printers.values()]
        for entry in printers:
            bind = entry.get("bind") or "0.0.0.0"
            entry["pos_address"] = (ip if bind in ("0.0.0.0", "", "::") else bind)
            entry["pos_port"] = raw_port
        health_report = self.health()
        return {
            "version": self.version,
            "system": sysinfo.summary(),
            "raw_port": raw_port,
            "printers": printers,
            "overall_status": health_report["level"],
            "transports": runtime_report(),
            "discovery": self.discovery_snapshot(),
            "network": self.network_state(),
            "update": self.update_state(),
            "health": health_report,
            "uptime": time.time() - self.started_at,
        }

    def scan(self) -> List[Dict[str, Any]]:
        return scan_devices()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def test_print(self, printer_id: str, kind: str = "standard") -> Dict[str, Any]:
        runtime = self.printers.get(printer_id)
        if runtime is None:
            return {"ok": False, "error": f"unknown printer '{printer_id}'"}
        worker = runtime.worker
        capabilities = worker.capabilities or {}
        recommendation = capabilities.get("recommendation") or {}
        columns = int(recommendation.get("columns") or 42)
        codepage = str(recommendation.get("codepage") or "cp1252")
        font_name = str(recommendation.get("font") or "font1")
        font_index = 1 if font_name.endswith("2") else 0
        features = capabilities.get("features") or {}

        def feature_on(name: str) -> bool:
            return bool((features.get(name) or {}).get("effective", False))

        ip = sysinfo.primary_ipv4()
        bind = runtime.config.get("bind") or "0.0.0.0"
        address = ip if bind in ("0.0.0.0", "", "::") else bind
        raw_port = runtime.raw_port

        if kind == "features":
            payload = escpos.feature_test_page(
                columns=columns,
                codepage=codepage,
                with_barcode=feature_on("barcode"),
                with_qr=feature_on("qrcode"),
                do_cut=feature_on("cutter"),
            )
        elif kind == "minimal":
            payload = (
                escpos.INIT
                + escpos.encode_text("BonBridge Testdruck OK\n\n\n", codepage)
                + (escpos.cut() if feature_on("cutter") else escpos.feed(4))
            )
        else:
            payload = escpos.test_page(
                title="BonBridge Testseite",
                printer_name=str(runtime.config.get("name") or printer_id),
                connection=f"{address}:{raw_port}",
                model=str(capabilities.get("profile_name") or ""),
                columns=columns,
                font=font_index,
                codepage=codepage,
                extra_lines=[
                    f"Geraet:       {sysinfo.hostname()}",
                    f"BonBridge:    {self.version}",
                ],
                qr_payload=f"http://{address}:{(self.config.data.get('web') or {}).get('port', 8080)}/",
                do_cut=feature_on("cutter"),
            )

        worker.submit_bytes(payload, source="web-ui", label=f"test:{kind}")
        return {"ok": True, "queued": True, "bytes": len(payload), "kind": kind}

    def probe(self, printer_id: str, what: str) -> Dict[str, Any]:
        """Active hardware probes that the user triggers explicitly."""
        runtime = self.printers.get(printer_id)
        if runtime is None:
            return {"ok": False, "error": f"unknown printer '{printer_id}'"}
        worker = runtime.worker
        if what == "cut":
            payload = escpos.feed(4) + escpos.cut("partial", feed_lines=2)
        elif what == "drawer":
            pin = int((runtime.config.get("options") or {}).get("drawer_pin") or 0)
            payload = escpos.drawer_pulse(pin)
        elif what == "buzzer":
            payload = escpos.buzzer()
        elif what == "feed":
            payload = escpos.feed(4)
        else:
            return {"ok": False, "error": f"unknown probe '{what}'"}
        worker.submit_bytes(payload, source="web-ui", label=f"probe:{what}")
        return {"ok": True, "queued": True, "probe": what}

    def raw_send(self, printer_id: str, data: bytes, label: str = "manual") -> Dict[str, Any]:
        runtime = self.printers.get(printer_id)
        if runtime is None:
            return {"ok": False, "error": f"unknown printer '{printer_id}'"}
        runtime.worker.submit_bytes(data, source="web-ui", label=label)
        return {"ok": True, "bytes": len(data)}

    def refresh(self, printer_id: str) -> Dict[str, Any]:
        runtime = self.printers.get(printer_id)
        if runtime is None:
            return {"ok": False, "error": f"unknown printer '{printer_id}'"}
        runtime.worker.refresh_status()
        return {"ok": True, **runtime.snapshot()}

    def redetect(self, printer_id: str) -> Dict[str, Any]:
        runtime = self.printers.get(printer_id)
        if runtime is None:
            return {"ok": False, "error": f"unknown printer '{printer_id}'"}
        worker = runtime.worker
        try:
            worker._drop_transport("re-detection requested")  # noqa: SLF001 - internal by design
            worker._ensure_transport()  # noqa: SLF001
            worker.refresh_status()
            return {"ok": True, **runtime.snapshot()}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}

    def integration_info(self, printer_id: str) -> Dict[str, Any]:
        """Everything the user needs to type into a POS application."""
        runtime = self.printers.get(printer_id)
        if runtime is None:
            return {"error": f"unknown printer '{printer_id}'"}
        ip = sysinfo.primary_ipv4()
        bind = runtime.config.get("bind") or "0.0.0.0"
        address = ip if bind in ("0.0.0.0", "", "::") else bind
        capabilities = runtime.worker.capabilities or {}
        recommendation = capabilities.get("recommendation") or {}
        return {
            "printer_id": printer_id,
            "name": runtime.config.get("name"),
            "ip": address,
            "port": runtime.raw_port,
            "protocol": "RAW / ESC-POS (JetDirect)",
            "recommendation": recommendation,
            "profile": capabilities.get("profile_name"),
            "hostname": sysinfo.hostname(),
        }

    def support_report(self) -> str:
        """Plain text report the user can paste into a support request."""
        lines: List[str] = []
        overview = self.overview()
        system = overview["system"]
        lines.append("BonBridge support report")
        lines.append("=" * 60)
        lines.append(f"Version:      {overview['version']}")
        lines.append(f"Generated:    {time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Host:         {system['hostname']}  ({system['model']})")
        lines.append(f"OS:           {system['os']} / kernel {system['kernel']} / {system['architecture']}")
        lines.append(f"Python:       {system['python']}")
        lines.append(f"Primary IP:   {system['primary_ip']}")
        temp = system.get("cpu_temperature")
        if temp:
            lines.append(f"CPU temp:     {temp:.1f} C")
        lines.append("")
        lines.append("Transports")
        lines.append("-" * 60)
        for name, info in overview["transports"].items():
            lines.append(f"  {name:<8} available={info['available']}  ({info['hint']})")
        lines.append("")
        for printer in overview["printers"]:
            lines.append(f"Printer '{printer['name']}' ({printer['id']})")
            lines.append("-" * 60)
            lines.append(f"  enabled:      {printer['enabled']}")
            lines.append(f"  connected:    {printer['connected']}")
            lines.append(f"  connection:   {printer['connection']}")
            lines.append(f"  POS address:  {printer.get('pos_address')}:{printer.get('pos_port')}")
            listener = printer.get("listener") or {}
            lines.append(
                f"  listener:     {listener.get('bind')}:{listener.get('port')} "
                f"listening={listener.get('listening')} error={listener.get('error')}"
            )
            status_text = "; ".join(escpos.status_texts(printer.get("status_messages") or [], "en"))
            lines.append(f"  status:       {printer['status_level']} - {status_text}")
            drawer = printer.get("drawer") or {}
            lines.append(
                f"  drawer:       {drawer.get('state', 'unknown')} (pin_high={drawer.get('pin_high')})"
            )
            lines.append(f"  jobs:         {printer['jobs_total']} ok / {printer['jobs_failed']} failed")
            lines.append(f"  queued:       {printer['queued']}  spooled: {printer['spooled']}")
            lines.append(f"  last error:   {printer['last_error']}")
            capabilities = printer.get("capabilities") or {}
            lines.append(f"  profile:      {capabilities.get('profile_name')} ({capabilities.get('profile_id')})")
            identity = printer.get("identity") or {}
            lines.append(f"  identity:     {identity.get('manufacturer', '')} {identity.get('product', '')}")
            lines.append(f"  GS I:         {identity.get('gs_i')}")
            recommendation = capabilities.get("recommendation") or {}
            lines.append(
                f"  POS settings: font={recommendation.get('font')} "
                f"columns={recommendation.get('columns')} codepage={recommendation.get('codepage')}"
            )
            features = capabilities.get("features") or {}
            for key, entry in features.items():
                lines.append(
                    f"    - {key:<16} detected={entry.get('detected')} "
                    f"override={entry.get('override')} effective={entry.get('effective')}"
                )
            lines.append("")

        report = self.health()
        lines.append("Health checks")
        lines.append("-" * 60)
        lines.append(f"  overall: {report['level']}")
        for check in report["device"]["checks"]:
            lines.append(f"  [{check['level']:<5}] device  {check['title_en']}")
            if check["detail_en"]:
                lines.append(f"            {check['detail_en']}")
        for printer_id, entry in report["printers"].items():
            for check in entry["checks"]:
                lines.append(f"  [{check['level']:<5}] {printer_id:<8} {check['title_en']}")
                if check["detail_en"]:
                    lines.append(f"            {check['detail_en']}")
        lines.append("")

        discovery_info = self.discovery_snapshot()
        enpc = discovery_info.get("enpc") or {}
        lines.append("Discovery")
        lines.append("-" * 60)
        lines.append(f"  mDNS active:   {discovery_info.get('mdns_active')}")
        lines.append(f"  ENPC enabled:  {enpc.get('enabled')}  listening={enpc.get('listening')}")
        lines.append(f"  ENPC probes:   {enpc.get('requests', 0)} received / {enpc.get('replies', 0)} answered")
        for probe in (enpc.get("probes") or [])[:5]:
            lines.append(f"  --- probe from {probe['peer']} ({probe['bytes']} bytes) ---")
            lines.append(probe["hexdump"])
        lines.append("")

        lines.append("Detected devices")
        lines.append("-" * 60)
        for device in self.scan():
            lines.append(f"  {device.get('transport'):<7} {device.get('label')}")
        lines.append("")
        lines.append("System diagnostics")
        lines.append("=" * 60)
        for name, output in sysinfo.diagnostics().items():
            lines.append(f"--- {name} ---")
            lines.append(output)
            lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Automatic slips, health, composing
    # ------------------------------------------------------------------

    def printer_address(self, runtime: "PrinterRuntime") -> str:
        """The address a POS application has to be pointed at."""
        bind = str(runtime.config.get("bind") or "0.0.0.0")
        if bind in ("0.0.0.0", "", "::"):
            return sysinfo.primary_ipv4()
        return bind

    def build_startup_report(self, worker: Any) -> bytes:
        """The slip printed on start-up: IP address, port and POS settings.

        A BonBridge device usually has no screen.  Printing its own address on
        power-up is the fastest way to get someone from "it is plugged in" to
        "the app can reach it" without a laptop.
        """
        runtime = self.printers.get(getattr(worker, "printer_id", ""))
        capabilities = getattr(worker, "capabilities", {}) or {}
        recommendation = capabilities.get("recommendation") or {}
        features = capabilities.get("features") or {}
        columns = int(recommendation.get("columns") or 42)
        codepage = str(recommendation.get("codepage") or "cp1252")
        font_name = str(recommendation.get("font") or "font1")
        font_index = 1 if font_name.endswith("2") else 0

        address = self.printer_address(runtime) if runtime else sysinfo.primary_ipv4()
        raw_port = runtime.raw_port if runtime else 9100
        web_port = int((self.config.data.get("web") or {}).get("port") or 8080)
        language = str((self.config.data.get("web") or {}).get("language") or "de")
        german = language.lower().startswith("de")

        if german:
            title = "BonBridge bereit"
            big_label = "IP-Adresse fuer das Kassensystem"
            rows = [
                ("Port", str(raw_port)),
                ("Drucker", str(getattr(worker, "config", {}).get("name") or "")),
                ("Modell", str(capabilities.get("profile_name") or "-")),
                ("Schriftart", str(recommendation.get("font") or "-")),
                ("Zeichensatz", codepage),
                ("Zeilenbreite", str(columns)),
                ("Geraet", sysinfo.hostname()),
                ("Version", self.version),
                ("Zeit", time.strftime("%Y-%m-%d %H:%M")),
            ]
            hints = [
                f"Weboberflaeche: http://{address}:{web_port}/",
                "In OrderAssist: Drucker -> + Hinzufuegen -> diese IP eintragen.",
                "Der Port ist in der App fest 9100 und muss nicht angegeben werden.",
                "Diesen Ausdruck kann man in der Weboberflaeche unter Drucker abschalten.",
            ]
        else:
            title = "BonBridge ready"
            big_label = "IP address for the POS application"
            rows = [
                ("Port", str(raw_port)),
                ("Printer", str(getattr(worker, "config", {}).get("name") or "")),
                ("Model", str(capabilities.get("profile_name") or "-")),
                ("Font", str(recommendation.get("font") or "-")),
                ("Character set", codepage),
                ("Line width", str(columns)),
                ("Device", sysinfo.hostname()),
                ("Version", self.version),
                ("Time", time.strftime("%Y-%m-%d %H:%M")),
            ]
            hints = [
                f"Web interface: http://{address}:{web_port}/",
                "In the POS app add a network printer with this IP address.",
                "The port is fixed at 9100 and does not need to be entered.",
                "This slip can be switched off in the web interface under Printers.",
            ]

        return escpos.status_report_page(
            title=title,
            lines=rows,
            hints=hints,
            columns=columns,
            font=font_index,
            codepage=codepage,
            qr_payload=f"http://{address}:{web_port}/",
            do_cut=bool((features.get("cutter") or {}).get("effective", True)),
            big_value=address,
            big_label=big_label,
        )

    def print_startup_report(self, printer_id: str) -> Dict[str, Any]:
        """Print the start-up slip again on demand."""
        runtime = self.printers.get(printer_id)
        if runtime is None:
            return {"ok": False, "error": f"unknown printer '{printer_id}'"}
        payload = self.build_startup_report(runtime.worker)
        runtime.worker.submit_bytes(payload, source="web-ui", label="startup-report")
        return {"ok": True, "queued": True, "bytes": len(payload)}

    def health(self) -> Dict[str, Any]:
        """Device health plus per-printer health, each with reasons."""
        device = health.summary(health.device_checks(self))
        printers = {}
        for printer_id, runtime in self.printers.items():
            printers[printer_id] = health.summary(health.printer_checks(runtime.snapshot()))
        levels = [device["level"]] + [entry["level"] for entry in printers.values()]
        return {
            "level": health.worst_level(levels),
            "device": device,
            "printers": printers,
        }

    def check_drawer(self, printer_id: str) -> Dict[str, Any]:
        """Active cash drawer test - fires the pulse and watches the pin."""
        runtime = self.printers.get(printer_id)
        if runtime is None:
            return {"ok": False, "error": f"unknown printer '{printer_id}'"}
        worker = runtime.worker
        transport = worker.transport
        if transport is None or not transport.is_open:
            return {"ok": False, "error": "printer not connected"}
        pin = int((runtime.config.get("options") or {}).get("drawer_pin") or 0)
        result = caps.probe_drawer(transport, pin=pin)
        if result["verdict"] in (caps.DRAWER_CONNECTED_CLOSED, caps.DRAWER_CONNECTED_OPEN):
            worker.note_drawer_seen()
        worker.refresh_status()
        return {"ok": True, "result": result, "drawer": worker.drawer}

    def compose(self, printer_id: str, spec: Dict[str, Any], do_print: bool = False) -> Dict[str, Any]:
        """Build a receipt from a spec; preview it and optionally print it."""
        runtime = self.printers.get(printer_id)
        if runtime is None:
            return {"ok": False, "error": f"unknown printer '{printer_id}'"}
        capabilities = runtime.worker.capabilities or {}
        recommendation = capabilities.get("recommendation") or {}
        features = capabilities.get("features") or {}

        def feature_on(name: str, default: bool = True) -> bool:
            return bool((features.get(name) or {}).get("effective", default))

        columns = int(spec.get("columns") or recommendation.get("columns") or 42)
        columns = max(16, min(96, columns))
        codepage = str(recommendation.get("codepage") or "cp1252")
        font_name = str(recommendation.get("font") or "font1")
        font_index = 1 if font_name.endswith("2") else 0

        payload, preview, notes = receipts.compose(
            spec,
            columns=columns,
            codepage=codepage,
            font=font_index,
            can_cut=feature_on("cutter"),
            can_drawer=feature_on("cashdrawer"),
            can_barcode=feature_on("barcode"),
            can_qr=feature_on("qrcode"),
        )

        result: Dict[str, Any] = {
            "ok": True,
            "columns": columns,
            "codepage": codepage,
            "font": font_name,
            "preview": preview,
            "notes": notes,
            "bytes": len(payload),
            "printed": False,
        }
        if do_print:
            runtime.worker.submit_bytes(payload, source="web-ui", label="composed receipt")
            result["printed"] = True
        return result

    # ------------------------------------------------------------------
    # Printing images
    # ------------------------------------------------------------------

    def prepare_image(
        self, printer_id: str, data: bytes, options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Rasterise an uploaded image and return the exact preview bitmap."""
        runtime = self.printers.get(printer_id)
        if runtime is None:
            return {"ok": False, "error": f"unknown printer '{printer_id}'"}
        kind, detail = images.sniff(data)
        if kind == "pdf":
            return {
                "ok": False,
                "error": (
                    "PDF wird nicht unterstuetzt - bitte vorher als PNG exportieren. / "
                    "PDF is not supported - please export it as a PNG first."
                ),
            }
        if not images.HAVE_PIL:
            return {"ok": False, "error": images.availability()["hint_en"]}

        capabilities = runtime.worker.capabilities or {}
        dots = images.dots_for_profile(capabilities)
        try:
            result = images.rasterise(
                data,
                dots=dots,
                scale_percent=int(options.get("scale") or 100),
                dither=bool(options.get("dither", True)),
                threshold=int(options.get("threshold") or 128),
                invert=bool(options.get("invert", False)),
                align=str(options.get("align") or "center"),
            )
        except Exception as exc:  # noqa: BLE001 - user-supplied file
            return {"ok": False, "error": str(exc)}

        features = capabilities.get("features") or {}
        payload = bytearray(escpos.INIT)
        payload += result["escpos"]
        payload += escpos.feed(int(options.get("feed") or 1))
        if options.get("cut", True):
            if (features.get("cutter") or {}).get("effective", True):
                payload += escpos.cut("partial", feed_lines=4)
            else:
                payload += escpos.feed(4)
                result["notes"].append("cutter_unsupported")

        token = f"{printer_id}:{int(time.time() * 1000)}"
        with self._lock:
            self._image_cache[token] = {
                "payload": bytes(payload),
                "printer_id": printer_id,
                "created": time.time(),
            }
            # Keep the cache tiny: this holds raw bitmaps.
            for key in sorted(self._image_cache)[:-3]:
                self._image_cache.pop(key, None)

        return {
            "ok": True,
            "token": token,
            "preview_png": result["preview_png"],
            "width": result["width"],
            "height": result["height"],
            "dots": dots,
            "bytes": len(payload),
            "format": detail or result["format"],
            "notes": result["notes"],
        }

    def print_image(self, printer_id: str, token: str) -> Dict[str, Any]:
        runtime = self.printers.get(printer_id)
        if runtime is None:
            return {"ok": False, "error": f"unknown printer '{printer_id}'"}
        with self._lock:
            entry = self._image_cache.get(token)
        if not entry or entry["printer_id"] != printer_id:
            return {"ok": False, "error": "preview expired - please upload the image again"}
        runtime.worker.submit_bytes(entry["payload"], source="web-ui", label="image")
        return {"ok": True, "queued": True, "bytes": len(entry["payload"])}

    def discovery_snapshot(self) -> Dict[str, Any]:
        settings = self.config.data.get("discovery") or {}
        return {
            "mdns": bool(settings.get("mdns", True)),
            "mdns_active": self.mdns.active,
            "enpc": self.enpc.snapshot()
            if self.enpc
            else {"enabled": False, "probes": [], "requests": 0, "replies": 0},
        }

    def clear_discovery_probes(self) -> Dict[str, Any]:
        if self.enpc is None:
            return {"ok": True, "removed": 0}
        return {"ok": True, "removed": self.enpc.clear_probes()}

    # ------------------------------------------------------------------
    # Configuration changes
    # ------------------------------------------------------------------

    def save_config(self) -> None:
        self.config.save()

    def profiles(self) -> List[Dict[str, Any]]:
        return caps.list_profiles()
