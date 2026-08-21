"""Small dependency-free web interface and REST API.

Deliberately built on :mod:`http.server` from the standard library: a print
bridge should not need a web framework, and on a Pi Zero 2 W every avoided
dependency is start-up time.  The UI itself is a single HTML file with vanilla
JavaScript that talks to the JSON API below.

The interface is intentionally **unauthenticated** and meant for the local
network only, as configured for this deployment.  Do not expose port 8080 to
the internet.
"""

from __future__ import annotations

import json
import logging
import mimetypes
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlparse

from .. import __version__, markdown, paths, sysinfo

log = logging.getLogger(__name__)

#: (method, compiled pattern, handler).  ``re.Pattern`` rather than
#: ``typing.Pattern`` - the latter was removed in Python 3.12.  The forward
#: reference keeps the subscript unevaluated so Python 3.8 stays happy too.
Route = Tuple[str, "re.Pattern[str]", Callable[..., Any]]


class ApiError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status
        self.message = message


class WebApplication:
    """Routing table plus handlers, bound to a :class:`~bonbridge.daemon.BonBridge`."""

    def __init__(self, app: Any):
        self.app = app
        self.routes: List[Route] = []
        self._register()

    # -- registration ------------------------------------------------------

    def route(self, method: str, pattern: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.routes.append((method, re.compile(f"^{pattern}$"), func))
            return func

        return decorator

    def dispatch(
        self, method: str, path: str, query: Dict[str, List[str]], body: Optional[bytes]
    ) -> Tuple[int, str, bytes]:
        for route_method, pattern, handler in self.routes:
            if route_method != method:
                continue
            match = pattern.match(path)
            if not match:
                continue
            try:
                result = handler(*match.groups(), query=query, body=body)
            except ApiError as exc:
                return exc.status, "application/json", _json({"ok": False, "error": exc.message})
            except Exception as exc:  # noqa: BLE001 - never leak a traceback to the LAN
                log.exception("API error on %s %s", method, path)
                return 500, "application/json", _json({"ok": False, "error": str(exc)})
            if isinstance(result, tuple):
                status, content_type, payload = result
                return status, content_type, payload
            return 200, "application/json", _json(result)
        return 404, "application/json", _json({"ok": False, "error": "not found"})

    # -- helpers -----------------------------------------------------------

    def _printer_config(self, printer_id: str) -> Dict[str, Any]:
        entry = self.app.config.printer(printer_id)
        if entry is None:
            raise ApiError(f"unknown printer '{printer_id}'", 404)
        return entry

    @staticmethod
    def _json_body(body: Optional[bytes]) -> Dict[str, Any]:
        if not body:
            return {}
        try:
            data = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ApiError(f"invalid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise ApiError("JSON body must be an object")
        return data

    # -- routes ------------------------------------------------------------

    def _register(self) -> None:  # noqa: C901 - a flat routing table is clearer
        app = self.app

        @self.route("GET", r"/api/overview")
        def overview(**_: Any) -> Dict[str, Any]:
            return app.overview()

        @self.route("GET", r"/healthz")
        def healthz(**_: Any) -> Dict[str, Any]:
            return {"ok": True, "version": __version__, "uptime": time.time() - app.started_at}

        @self.route("GET", r"/api/config")
        def get_config(**_: Any) -> Dict[str, Any]:
            return {"ok": True, "config": app.config.as_dict()}

        @self.route("PUT", r"/api/config")
        def put_config(*, body: Optional[bytes] = None, **_: Any) -> Dict[str, Any]:
            patch = self._json_body(body)
            allowed = {
                "web",
                "raw",
                "discovery",
                "logging",
                "hostname_label",
                "network_watch",
                "update",
            }
            unknown = set(patch) - allowed
            if unknown:
                raise ApiError(f"cannot change: {', '.join(sorted(unknown))}")
            for key, value in patch.items():
                if isinstance(value, dict) and isinstance(app.config.data.get(key), dict):
                    app.config.data[key].update(value)
                else:
                    app.config.data[key] = value
            app.save_config()
            # Discovery listeners bind their own ports, so changing them has to
            # rebind - otherwise "saved" would be a lie until the next reboot.
            if "discovery" in patch:
                app.restart_discovery()
            return {
                "ok": True,
                "restart_required": bool({"web", "raw"} & set(patch)),
                "config": app.config.as_dict(),
            }

        @self.route("GET", r"/api/printers")
        def list_printers(**_: Any) -> Dict[str, Any]:
            return {"ok": True, "printers": [r.snapshot() for r in app.printers.values()]}

        @self.route("POST", r"/api/printers")
        def add_printer(*, body: Optional[bytes] = None, **_: Any) -> Dict[str, Any]:
            entry = app.config.add_printer(self._json_body(body))
            app.save_config()
            app.restart_printers()
            return {"ok": True, "printer": entry, "restarted": True}

        @self.route("GET", r"/api/printers/([^/]+)")
        def get_printer(printer_id: str, **_: Any) -> Dict[str, Any]:
            runtime = app.runtime(printer_id)
            if runtime is None:
                raise ApiError(f"unknown printer '{printer_id}'", 404)
            return {"ok": True, "printer": runtime.snapshot(), "config": self._printer_config(printer_id)}

        @self.route("PATCH", r"/api/printers/([^/]+)")
        def patch_printer(printer_id: str, *, body: Optional[bytes] = None, **_: Any) -> Dict[str, Any]:
            self._printer_config(printer_id)
            patch = self._json_body(body)
            updated = app.config.update_printer(printer_id, patch)
            app.save_config()
            app.restart_printers()
            return {"ok": True, "printer": updated, "restarted": True}

        @self.route("DELETE", r"/api/printers/([^/]+)")
        def delete_printer(printer_id: str, **_: Any) -> Dict[str, Any]:
            if not app.config.remove_printer(printer_id):
                raise ApiError(f"unknown printer '{printer_id}'", 404)
            app.save_config()
            app.restart_printers()
            return {"ok": True, "removed": printer_id}

        @self.route("POST", r"/api/printers/([^/]+)/test")
        def test_print(printer_id: str, *, body: Optional[bytes] = None, **_: Any) -> Dict[str, Any]:
            payload = self._json_body(body)
            return app.test_print(printer_id, str(payload.get("kind") or "standard"))

        @self.route("POST", r"/api/printers/([^/]+)/probe")
        def probe(printer_id: str, *, body: Optional[bytes] = None, **_: Any) -> Dict[str, Any]:
            payload = self._json_body(body)
            what = str(payload.get("what") or "")
            if not what:
                raise ApiError("missing 'what'")
            return app.probe(printer_id, what)

        @self.route("POST", r"/api/printers/([^/]+)/raw")
        def raw(printer_id: str, *, body: Optional[bytes] = None, **_: Any) -> Dict[str, Any]:
            payload = self._json_body(body)
            if "hex" in payload:
                cleaned = re.sub(r"[^0-9a-fA-F]", "", str(payload["hex"]))
                if len(cleaned) % 2:
                    raise ApiError("hex string has an odd number of digits")
                data = bytes.fromhex(cleaned)
            elif "text" in payload:
                data = str(payload["text"]).replace("\\n", "\n").encode("cp437", "replace")
            else:
                raise ApiError("provide 'hex' or 'text'")
            if len(data) > 65536:
                raise ApiError("payload too large (max 64 KiB)")
            return app.raw_send(printer_id, data, label="manual")

        @self.route("POST", r"/api/printers/([^/]+)/refresh")
        def refresh(printer_id: str, **_: Any) -> Dict[str, Any]:
            return app.refresh(printer_id)

        @self.route("POST", r"/api/printers/([^/]+)/redetect")
        def redetect(printer_id: str, **_: Any) -> Dict[str, Any]:
            return app.redetect(printer_id)

        @self.route("POST", r"/api/printers/([^/]+)/spool/clear")
        def clear_spool(printer_id: str, **_: Any) -> Dict[str, Any]:
            runtime = app.runtime(printer_id)
            if runtime is None:
                raise ApiError(f"unknown printer '{printer_id}'", 404)
            return {"ok": True, "removed": runtime.worker.clear_spool()}

        @self.route("GET", r"/api/printers/([^/]+)/integration")
        def integration(printer_id: str, **_: Any) -> Dict[str, Any]:
            return {"ok": True, "integration": app.integration_info(printer_id)}

        @self.route("GET", r"/api/health")
        def health_route(**_: Any) -> Dict[str, Any]:
            return {"ok": True, "health": app.health()}

        @self.route("GET", r"/api/discovery")
        def discovery_route(**_: Any) -> Dict[str, Any]:
            return {"ok": True, "discovery": app.discovery_snapshot()}

        @self.route("POST", r"/api/discovery/clear")
        def discovery_clear(**_: Any) -> Dict[str, Any]:
            return app.clear_discovery_probes()

        @self.route("POST", r"/api/printers/([^/]+)/drawer-check")
        def drawer_check(printer_id: str, **_: Any) -> Dict[str, Any]:
            return app.check_drawer(printer_id)

        @self.route("POST", r"/api/printers/([^/]+)/startup-report")
        def startup_report(printer_id: str, **_: Any) -> Dict[str, Any]:
            return app.print_startup_report(printer_id)

        @self.route("POST", r"/api/printers/([^/]+)/compose")
        def compose(printer_id: str, *, body: Optional[bytes] = None, **_: Any) -> Dict[str, Any]:
            payload = self._json_body(body)
            spec = payload.get("spec")
            if not isinstance(spec, dict):
                raise ApiError("missing 'spec' object")
            return app.compose(printer_id, spec, do_print=bool(payload.get("print")))

        # -- network watchdog ------------------------------------------

        @self.route("GET", r"/api/network")
        def network_route(**_: Any) -> Dict[str, Any]:
            return {"ok": True, "network": app.network_state()}

        @self.route("POST", r"/api/network/check")
        def network_check_route(**_: Any) -> Dict[str, Any]:
            return app.check_network()

        @self.route("POST", r"/api/printers/([^/]+)/network-test")
        def network_test(printer_id: str, *, body: Optional[bytes] = None, **_: Any) -> Dict[str, Any]:
            payload = self._json_body(body)
            return app.test_network_alert(printer_id, bool(payload.get("online")))

        # -- software updates ------------------------------------------

        @self.route("GET", r"/api/update")
        def update_route(**_: Any) -> Dict[str, Any]:
            return {"ok": True, "update": app.update_state()}

        @self.route("POST", r"/api/update/check")
        def update_check(**_: Any) -> Dict[str, Any]:
            return app.check_update()

        @self.route("GET", r"/api/update/log")
        def update_log(*, query: Optional[Dict[str, List[str]]] = None, **_: Any) -> Dict[str, Any]:
            try:
                lines = int((query or {}).get("lines", ["200"])[0])
            except ValueError:
                lines = 200
            return app.update_log(max(10, min(2000, lines)))

        @self.route("POST", r"/api/update/install")
        def update_install(*, body: Optional[bytes] = None, **_: Any) -> Dict[str, Any]:
            payload = self._json_body(body)
            try:
                return app.start_update(
                    str(payload.get("source") or "online"), str(payload.get("file") or "")
                )
            except PermissionError as exc:
                raise ApiError(str(exc), 403) from exc

        @self.route("POST", r"/api/update/upload")
        def update_upload(
            *, query: Optional[Dict[str, List[str]]] = None, body: Optional[bytes] = None, **_: Any
        ) -> Dict[str, Any]:
            if not body:
                raise ApiError("no file received")
            name = (query or {}).get("name", ["update.tar.gz"])[0]
            try:
                return app.store_upload(name, body)
            except PermissionError as exc:
                raise ApiError(str(exc), 403) from exc

        # -- printing an image -----------------------------------------

        @self.route("GET", r"/api/image/support")
        def image_support(**_: Any) -> Dict[str, Any]:
            from .. import images

            return {"ok": True, "support": images.availability()}

        @self.route("POST", r"/api/printers/([^/]+)/image")
        def image_prepare(
            printer_id: str,
            *,
            query: Optional[Dict[str, List[str]]] = None,
            body: Optional[bytes] = None,
            **_: Any,
        ) -> Dict[str, Any]:
            if not body:
                raise ApiError("no image received")
            params = query or {}

            def flag(name: str, default: bool) -> bool:
                raw = params.get(name, [None])[0]
                if raw is None:
                    return default
                return raw not in ("0", "false", "no")

            def number(name: str, default: int) -> int:
                try:
                    return int(params.get(name, [str(default)])[0])
                except ValueError:
                    return default

            return app.prepare_image(
                printer_id,
                body,
                {
                    "scale": number("scale", 100),
                    "threshold": number("threshold", 128),
                    "feed": number("feed", 1),
                    "dither": flag("dither", True),
                    "invert": flag("invert", False),
                    "cut": flag("cut", True),
                    "align": params.get("align", ["center"])[0],
                },
            )

        @self.route("POST", r"/api/printers/([^/]+)/image/print")
        def image_print(printer_id: str, *, body: Optional[bytes] = None, **_: Any) -> Dict[str, Any]:
            payload = self._json_body(body)
            token = str(payload.get("token") or "")
            if not token:
                raise ApiError("missing 'token'")
            return app.print_image(printer_id, token)

        @self.route("GET", r"/api/scan")
        def scan(**_: Any) -> Dict[str, Any]:
            return {"ok": True, "devices": app.scan()}

        @self.route("GET", r"/api/profiles")
        def profiles(**_: Any) -> Dict[str, Any]:
            return {"ok": True, "profiles": app.profiles()}

        @self.route("GET", r"/api/diagnostics")
        def diagnostics(**_: Any) -> Dict[str, Any]:
            return {"ok": True, "system": sysinfo.summary(), "commands": sysinfo.diagnostics()}

        @self.route("GET", r"/api/report")
        def report(**_: Any) -> Tuple[int, str, bytes]:
            text = app.support_report()
            return 200, "text/plain; charset=utf-8", text.encode("utf-8")

        @self.route("POST", r"/api/restart")
        def restart(**_: Any) -> Dict[str, Any]:
            app.restart_printers()
            return {"ok": True}

        @self.route("GET", r"/docs")
        def docs_index(*, query: Optional[Dict[str, List[str]]] = None, **_: Any) -> Tuple[int, str, bytes]:
            language = (query or {}).get("lang", ["de"])[0]
            language = language if language in ("de", "en") else "de"
            return 200, "text/html; charset=utf-8", _docs_index_html(language)

        @self.route("GET", r"/docs/(de|en)/([A-Za-z0-9._-]+)")
        def docs_page(language: str, name: str, **_: Any) -> Tuple[int, str, bytes]:
            if name.endswith(".html"):
                name = name[: -len(".html")] + ".md"
            if not name.endswith(".md"):
                name += ".md"
            path = (paths.DOCS_DIR / language / name).resolve()
            root = paths.DOCS_DIR.resolve()
            if not str(path).startswith(str(root)) or not path.is_file():
                raise ApiError("document not found", 404)
            source = path.read_text(encoding="utf-8")
            page = markdown.render_document(
                source,
                css=DOC_CSS,
                link_rewriter=_make_link_rewriter(language),
                nav_html=_docs_nav_html(language, name),
                language=language,
            )
            return 200, "text/html; charset=utf-8", page.encode("utf-8")

        @self.route("GET", r"/docs-img/([A-Za-z0-9._-]+)")
        def docs_image(name: str, **_: Any) -> Tuple[int, str, bytes]:
            path = (paths.DOCS_DIR / "img" / name).resolve()
            root = (paths.DOCS_DIR / "img").resolve()
            if not str(path).startswith(str(root)) or not path.is_file():
                raise ApiError("image not found", 404)
            content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
            if content_type == "image/svg+xml":
                content_type += "; charset=utf-8"
            return 200, content_type, path.read_bytes()

        @self.route("GET", r"/api/docs")
        def docs_list(**_: Any) -> Dict[str, Any]:
            return {"ok": True, "documents": _list_docs()}

        @self.route("GET", r"/api/docs/(de|en)/([A-Za-z0-9._-]+)")
        def docs_read(language: str, name: str, **_: Any) -> Tuple[int, str, bytes]:
            path = (paths.DOCS_DIR / language / name).resolve()
            root = paths.DOCS_DIR.resolve()
            if not str(path).startswith(str(root)) or not path.is_file():
                raise ApiError("document not found", 404)
            return 200, "text/markdown; charset=utf-8", path.read_bytes()


DOC_CSS = """
:root{--bg:#f5f6f8;--panel:#fff;--panel2:#f0f2f5;--line:#dfe3e9;--fg:#1a1d23;
      --muted:#5b6472;--accent:#2f6fd0;--radius:10px}
@media (prefers-color-scheme: dark){
  :root{--bg:#0f1115;--panel:#171a21;--panel2:#1e222b;--line:#2a2f3a;--fg:#e8eaed;
        --muted:#9aa3b2;--accent:#4f9cf9}
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
     font:16px/1.65 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
header.docnav{position:sticky;top:0;z-index:5;background:var(--panel);
  border-bottom:1px solid var(--line);padding:.6rem 1rem;display:flex;gap:.5rem;
  align-items:center;flex-wrap:wrap}
header.docnav a{color:var(--muted);text-decoration:none;font-size:.86rem;
  padding:.25rem .55rem;border-radius:var(--radius);border:1px solid transparent}
header.docnav a:hover{background:var(--panel2);color:var(--fg)}
header.docnav a.active{background:var(--panel2);color:var(--fg);border-color:var(--line)}
header.docnav .brand{font-weight:700;margin-right:.6rem;color:var(--fg)}
header.docnav .spacer{flex:1}
main.doc{max-width:60rem;margin:0 auto;padding:1.4rem 1.2rem 4rem}
article{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
  padding:1.4rem 1.6rem;overflow-wrap:break-word}
h1,h2,h3,h4{line-height:1.25;margin:1.8rem 0 .6rem}
h1{margin-top:0;font-size:1.7rem}
h2{font-size:1.3rem;border-bottom:1px solid var(--line);padding-bottom:.3rem}
h3{font-size:1.08rem;color:var(--muted);text-transform:none}
a{color:var(--accent)}
a.anchor{opacity:0;margin-left:.4rem;text-decoration:none;font-weight:400}
h1:hover a.anchor,h2:hover a.anchor,h3:hover a.anchor{opacity:.45}
code{background:var(--panel2);border:1px solid var(--line);border-radius:5px;
  padding:.06rem .32rem;font-size:.88em}
pre{background:var(--panel2);border:1px solid var(--line);border-radius:var(--radius);
  padding:.9rem 1rem;overflow:auto;font-size:.84rem;line-height:1.45}
pre code{background:none;border:none;padding:0;font-size:inherit}
table{border-collapse:collapse;width:100%;margin:1rem 0;font-size:.92rem;display:block;overflow-x:auto}
th,td{border:1px solid var(--line);padding:.42rem .6rem;vertical-align:top}
th{background:var(--panel2);text-align:left}
blockquote{margin:1rem 0;padding:.6rem 1rem;border-left:4px solid var(--accent);
  background:var(--panel2);border-radius:0 var(--radius) var(--radius) 0}
blockquote p{margin:.3rem 0}
img{max-width:100%;height:auto;background:#fff;border:1px solid var(--line);
  border-radius:var(--radius);padding:.5rem}
ul,ol{padding-left:1.4rem}
li{margin:.25rem 0}
hr{border:none;border-top:1px solid var(--line);margin:1.6rem 0}
nav.toc{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
  padding:.8rem 1rem;margin-bottom:1rem;font-size:.9rem}
nav.toc .toc-title{font-weight:600;margin-bottom:.35rem;color:var(--muted)}
nav.toc ul{list-style:none;padding-left:0;margin:0}
nav.toc li.lvl3{padding-left:1rem}
nav.toc a{text-decoration:none}
nav.toc a:hover{text-decoration:underline}
@media print{header.docnav,nav.toc{display:none}article{border:none;padding:0}}
"""

#: Documentation pages in reading order, per language.
DOC_PAGES = {
    "de": [
        ("01-hardware.md", "Hardware"),
        ("02-anschlussplan.md", "Anschlussplan"),
        ("03-drucker-konfiguration.md", "Drucker einrichten"),
        ("04-orderassist.md", "OrderAssist"),
        ("05-weboberflaeche.md", "Weboberfläche"),
        ("06-diagnose.md", "Diagnose"),
        ("07-ausdruckgruppen.md", "Mehrere Drucker"),
        ("08-architektur.md", "Architektur"),
        ("09-referenzen.md", "Referenzen"),
        ("10-updates.md", "Updates & Wartung"),
    ],
    "en": [
        ("01-hardware.md", "Hardware"),
        ("02-wiring.md", "Wiring"),
        ("03-printer-setup.md", "Printer setup"),
        ("04-pos-integration.md", "POS integration"),
        ("05-web-interface.md", "Web interface"),
        ("06-diagnostics.md", "Diagnostics"),
        ("07-print-groups.md", "Several printers"),
        ("08-architecture.md", "Architecture"),
        ("09-references.md", "References"),
        ("10-updates.md", "Updates & maintenance"),
    ],
}


def _make_link_rewriter(language: str):
    """Turn the Markdown links into links that work inside the web interface."""

    def rewrite(href: str, is_image: bool) -> str:
        if href.startswith(("http://", "https://", "mailto:", "#", "/")):
            return href
        target = href.split("#", 1)
        anchor = f"#{target[1]}" if len(target) > 1 else ""
        name = target[0]
        if is_image or name.endswith((".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp")):
            return "/docs-img/" + name.split("/")[-1]
        if name.endswith(".md"):
            plain = name.split("/")[-1]
            if name.startswith("../../") or "/" not in name.replace("../", ""):
                # sibling page inside the same language folder
                if name.startswith("../../"):
                    # repository root file such as MIGRATION.md - no HTML view
                    return "https://github.com/loe17/Bonbridge/blob/main/" + name.replace("../../", "")
                return f"/docs/{language}/{plain}{anchor}"
            return f"/docs/{language}/{plain}{anchor}"
        if name.startswith("../../"):
            return "https://github.com/loe17/Bonbridge/blob/main/" + name.replace("../../", "")
        return href

    return rewrite


def _docs_nav_html(language: str, current: str = "") -> str:
    import html as _html

    other = "en" if language == "de" else "de"
    home_label = "Zurück zur Oberfläche" if language == "de" else "Back to the interface"
    items = ['<a class="brand" href="/">BonBridge</a>', f'<a href="/">&larr; {home_label}</a>']
    items.append('<span class="spacer"></span>')
    for name, label in DOC_PAGES.get(language, []):
        active = ' class="active"' if name == current else ""
        items.append(f'<a href="/docs/{language}/{name}"{active}>{_html.escape(label)}</a>')
    items.append(f'<a href="/docs?lang={other}">{other.upper()}</a>')
    return f'<header class="docnav">{"".join(items)}</header>'


def _docs_index_html(language: str) -> bytes:
    import html as _html

    german = language == "de"
    title = "Dokumentation" if german else "Documentation"
    intro = (
        "Die vollständige BonBridge-Dokumentation, direkt auf dem Gerät - auch ohne "
        "Internetverbindung. Die Quelldateien liegen als Markdown im Repository."
        if german
        else "The complete BonBridge documentation, served from the device itself - no "
        "internet connection required. The sources are Markdown files in the repository."
    )
    cards = []
    for name, label in DOC_PAGES.get(language, []):
        path = paths.DOCS_DIR / language / name
        summary = ""
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith(("#", "!", ">", "|", "*", "-")):
                    summary = stripped
                    break
        except OSError:
            continue
        cards.append(
            f'<li><a href="/docs/{language}/{name}"><strong>{_html.escape(label)}</strong>'
            f'<span>{_html.escape(summary[:160])}</span></a></li>'
        )
    extra_css = """
    ul.cards{list-style:none;padding:0;display:grid;gap:.7rem;
             grid-template-columns:repeat(auto-fit,minmax(17rem,1fr))}
    ul.cards a{display:block;padding:.8rem 1rem;border:1px solid var(--line);
               border-radius:var(--radius);text-decoration:none;background:var(--panel2)}
    ul.cards a:hover{border-color:var(--accent)}
    ul.cards strong{display:block;color:var(--fg);margin-bottom:.2rem}
    ul.cards span{color:var(--muted);font-size:.86rem}
    """
    body = (
        f"<h1>{title}</h1><p>{_html.escape(intro)}</p>"
        f'<ul class="cards">{"".join(cards)}</ul>'
    )
    page = (
        "<!DOCTYPE html>"
        f'<html lang="{language}"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{title} - BonBridge</title><style>{DOC_CSS}{extra_css}</style></head><body>"
        f'{_docs_nav_html(language)}<main class="doc"><article>{body}</article></main>'
        "</body></html>"
    )
    return page.encode("utf-8")


def _list_docs() -> List[Dict[str, str]]:
    documents: List[Dict[str, str]] = []
    for language in ("de", "en"):
        directory = paths.DOCS_DIR / language
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.md")):
            title = path.stem
            try:
                for line in path.read_text(encoding="utf-8").splitlines():
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break
            except OSError:
                pass
            documents.append({"language": language, "file": path.name, "title": title})
    return documents


def _json(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, default=_fallback).encode("utf-8")


def _fallback(value: Any) -> Any:
    try:
        return str(value)
    except Exception:  # noqa: BLE001
        return None


class _RequestHandler(BaseHTTPRequestHandler):
    server_version = f"BonBridge/{__version__}"
    protocol_version = "HTTP/1.1"
    application: WebApplication  # set on the server class

    # -- plumbing ----------------------------------------------------------

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        log.debug("%s - %s", self.address_string(), fmt % args)

    def _send(self, status: int, content_type: str, payload: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _read_body(self) -> Optional[bytes]:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return None
        if length <= 0:
            return None
        # Large enough for an update archive or a photo, small enough that a
        # stray request cannot exhaust a Pi Zero's memory.
        if length > 48 * 1024 * 1024:
            return None
        return self.rfile.read(length)

    def _handle(self, method: str) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        query = parse_qs(parsed.query)

        if method == "GET" and (path == "/" or path.startswith("/static/") or path == "/favicon.ico"):
            self._serve_static(path)
            return

        body = self._read_body() if method in ("POST", "PUT", "PATCH") else None
        status, content_type, payload = self.server.application.dispatch(method, path, query, body)  # type: ignore[attr-defined]
        self._send(status, content_type, payload)

    def _serve_static(self, path: str) -> None:
        if path in ("/", ""):
            relative = "index.html"
        elif path == "/favicon.ico":
            relative = "favicon.svg"
        else:
            relative = path[len("/static/") :]
        target = (paths.WEB_STATIC_DIR / relative).resolve()
        root = paths.WEB_STATIC_DIR.resolve()
        if not str(target).startswith(str(root)) or not target.is_file():
            self._send(404, "text/plain; charset=utf-8", b"not found")
            return
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in (
            "application/javascript",
            "image/svg+xml",
        ):
            content_type += "; charset=utf-8"
        self._send(200, content_type, target.read_bytes())

    # -- verbs -------------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802
        self._handle("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._handle("POST")

    def do_PUT(self) -> None:  # noqa: N802
        self._handle("PUT")

    def do_PATCH(self) -> None:  # noqa: N802
        self._handle("PATCH")

    def do_DELETE(self) -> None:  # noqa: N802
        self._handle("DELETE")


class WebServer(threading.Thread):
    """Runs the HTTP interface in the background."""

    def __init__(self, app: Any, bind: str = "0.0.0.0", port: int = 8080):
        super().__init__(name="web", daemon=True)
        self.bind = bind
        self.port = port
        self.application = WebApplication(app)
        self.httpd: Optional[ThreadingHTTPServer] = None
        self.last_error: Optional[str] = None
        self._stop_event = threading.Event()

    def run(self) -> None:
        delay = 1.0
        while not self._stop_event.is_set():
            try:
                httpd = ThreadingHTTPServer((self.bind, self.port), _RequestHandler)
                httpd.daemon_threads = True
                httpd.application = self.application  # type: ignore[attr-defined]
                self.httpd = httpd
                self.last_error = None
                log.info("Web interface on http://%s:%s/", self.bind, self.port)
                delay = 1.0
            except OSError as exc:
                self.last_error = str(exc)
                log.warning("Cannot bind web interface to %s:%s: %s", self.bind, self.port, exc)
                self._stop_event.wait(delay)
                delay = min(delay * 2, 30.0)
                continue
            try:
                httpd.serve_forever(poll_interval=0.5)
            except Exception as exc:  # noqa: BLE001
                log.warning("Web interface crashed: %s", exc)
            finally:
                try:
                    httpd.server_close()
                except Exception:  # noqa: BLE001
                    pass
                self.httpd = None

    def stop(self) -> None:
        self._stop_event.set()
        if self.httpd is not None:
            try:
                self.httpd.shutdown()
            except Exception:  # noqa: BLE001
                pass
