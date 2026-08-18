"""The BonBridge daemon: wires printers, RAW listeners and the web interface."""

from __future__ import annotations

import logging
import signal
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from . import __version__, caps, discovery, escpos, mdns, paths, sysinfo
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
        self.web_server: Any = None
        self.version = __version__

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        paths.ensure_runtime_dirs()
        self._ensure_default_printer()
        self._start_printers()
        self._start_discovery()
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
        for printer_config in self.config.printers:
            runtime = PrinterRuntime(printer_config, raw_port, max_connections)
            self.printers[runtime.printer_id] = runtime
            runtime.start()

    def _start_discovery(self) -> None:
        settings = self.config.data.get("discovery") or {}
        web_port = int((self.config.data.get("web") or {}).get("port") or 8080)
        raw_port = int((self.config.data.get("raw") or {}).get("port") or 9100)
        announced = [
            {"id": p.printer_id, "name": p.config.get("name"), "port": raw_port}
            for p in self.printers.values()
            if p.config.get("enabled", True)
        ]
        if settings.get("mdns", True):
            mdns.write_avahi_service_file(
                announced, web_port, str(self.config.data.get("hostname_label") or "")
            )
            self.mdns.start(announced, web_port)
        if settings.get("enpc", False):
            self.enpc = discovery.EnpcResponder(
                device_name_provider=lambda: str(
                    self.config.data.get("hostname_label") or sysinfo.hostname()
                ),
                mac_provider=discovery.local_mac,
                ip_provider=sysinfo.primary_ipv4,
            )
            self.enpc.start()

    def stop(self) -> None:
        log.info("Shutting down")
        self._stop_event.set()
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
        worst = "ok"
        ranking = {"ok": 0, "warn": 1, "unknown": 1, "offline": 2, "error": 3}
        for entry in printers:
            if ranking.get(entry.get("status_level", "unknown"), 1) > ranking.get(worst, 0):
                worst = entry.get("status_level", "unknown")
        return {
            "version": self.version,
            "system": sysinfo.summary(),
            "raw_port": raw_port,
            "printers": printers,
            "overall_status": worst if printers else "unknown",
            "transports": runtime_report(),
            "discovery": {
                "mdns": bool((self.config.data.get("discovery") or {}).get("mdns", True)),
                "mdns_active": self.mdns.active,
                "enpc": self.enpc.snapshot() if self.enpc else {"enabled": False},
            },
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
            lines.append(f"  status:       {printer['status_level']} - {'; '.join(printer['status_messages'])}")
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
    # Configuration changes
    # ------------------------------------------------------------------

    def save_config(self) -> None:
        self.config.save()

    def profiles(self) -> List[Dict[str, Any]]:
        return caps.list_profiles()
