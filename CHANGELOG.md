# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/), and the
project uses [Semantic Versioning](https://semver.org/).

## [1.1.1] - 2026-08-18

### Fixed

- **Python 3.12 and 3.13 could not import the web server.** `typing.Pattern`
  was removed in Python 3.12; the routing table used it. Replaced with
  `re.Pattern`. This is why CI passed on 3.9 and 3.11 but failed on 3.13.
- **The discovery responder died on Python 3.13.** `threading.Thread` gained a
  private `_handle` attribute in 3.13, which silently overwrote the responder's
  method of the same name - the thread crashed with
  `'_thread._ThreadHandle' object is not callable` on the first probe. The
  method was renamed, and the same latent trap was removed everywhere else:
  three thread classes assigned `self._stop = Event()`, shadowing
  `Thread._stop`, which would break `join()` and `is_alive()`.
- Ruff findings cleaned up: unused imports, an f-string without placeholders,
  and two route handlers sharing a function name.

### Added

- **A structural test that makes this class of bug impossible to reintroduce.**
  It asserts that no `threading.Thread` subclass shadows a Thread attribute,
  on whatever Python version it runs - so a future release adding another
  private attribute is caught by the test rather than in production.
- **Python 3.12 added to the CI matrix** (3.9, 3.11, 3.12, 3.13). 3.12 is where
  `typing.Pattern` disappeared; testing it would have caught this before the
  release.

Verified by running the full end-to-end suite (66 checks) on real 3.9, 3.11,
3.12 and 3.13 interpreters.

## [1.1.0] - 2026-08-18

### Added

- **Status slip on start-up** (on by default). Every time the daemon starts,
  the printer produces a slip with its own IP address in double size, the port,
  the recommended POS settings and a QR code to the web interface. A BonBridge
  device has no screen; this is the fastest route from "plugged in" to "the app
  prints". Switchable per printer, and the setting lives in `config.yaml`, so it
  survives a power cut. *Overview → Print status slip* repeats it on demand.
- **Paper-low warning slip** (off by default). Prints a one-off notice when the
  roll reports "paper near end", and only prints again after new paper has been
  detected. The "already warned" flag is persisted, so a reboot does not
  reprint it.
- **Cash drawer: connected or not.** The feature list said "cash drawer:
  detected" even with nothing plugged in - correct but useless. The live state
  is now shown separately and honestly: a LOW pin proves a drawer is connected
  and closed; a HIGH pin means "open **or** absent", because the two are
  electrically identical. Once a LOW has been seen, the fact is remembered
  across power cuts. The new active test *Check cash drawer* reads the pin,
  fires the pulse and reads again - a LOW→HIGH change can only mean a real
  drawer.
- **Every warning is now explained.** New health engine with individual checks
  for Raspberry Pi under-voltage and throttling (`get_throttled`), CPU
  temperature, free disk space, free memory, missing Python bindings, the state
  of the network listener, printer status and spooled jobs. Each check carries a
  level, a title and advice in German and English, and expands under the traffic
  light in the interface and in *Diagnostics → All checks*. Also in the support
  report and via `GET /api/health`.
- **Print receipts from the web interface**, new *Print* tab: heading, content,
  footer, QR code, cut and drawer, with a **live preview** rendered in the real
  paper width of the detected printer. `---` becomes a divider and `text | value`
  puts the value flush right. Preview and print share one code path, so what is
  shown is what is printed; unsupported features are named and skipped instead
  of failing.
- **Documentation as HTML on the device** at `/docs`, with navigation, table of
  contents, images and print styling - rendered by a small Markdown converter
  written for this purpose (no new dependency). The `.md` files remain the
  source of truth.
- **Automatic printer search**: the Epson ENPC responder (UDP 3289) is now
  enabled by default and, more importantly, **every probe is logged with a
  hexdump** and shown in *Diagnostics → Automatic printer search*. Epson does
  not publish the protocol, so this makes the decisive question answerable in
  one attempt: does the app send anything at all? The mDNS announcement now also
  carries the Bonjour printing TXT records (`usb_MFG`, `usb_MDL`, `product`).
- **Tooltips on every input field**, explaining what it does and when to change
  it, in both languages.
- Serial numbers are shown in the device scan and taken over automatically,
  which is what keeps two identical printers apart.

### Changed

- **`0.0.0.0` for "IP address for port 9100" is now explained properly** - in
  the field tooltip, in an inline hint and in a dedicated documentation section:
  with one printer it is always right, and a fixed address is only needed when
  several printers share one device, because POS systems identify printers by IP
  alone.
- **Status messages are no longer English-only.** The daemon now stores message
  keys and the interface renders them, so the German UI no longer shows "Paper
  near end". Option labels, transport field labels, profile detection reasons
  and preview markers were translated as well.
- The device card shows the **device's own** health level; the aggregate that
  includes the printers is shown separately, so a yellow device light no longer
  appears without a device problem.
- Documentation: a step-by-step section on physically attaching several
  printers (power budget, powered USB hubs, identifying units by serial number),
  and a realistic note that `<hostname>.local` does not resolve on Windows
  without Bonjour - the IP address always does.

### Fixed

- **Right-aligned amounts were collapsed.** The word wrapper rebuilt lines on
  single spaces, which destroyed the padding of `key | value` lines - both in
  the preview and in the printed receipt. Lines that already fit are now left
  untouched, which also preserves deliberate indentation.
- The ENPC responder answered its own reply when the probe came from the same
  machine, cluttering the probe log. Local addresses are now excluded from the
  second reply target.

## [1.0.1] - 2026-08-18

### Fixed

- **Installer aborted where systemd is not PID 1.** `install.sh` called
  `systemctl daemon-reload` unconditionally, which fails inside Docker
  containers, CI runners and chroots ("System has not been booted with systemd
  as init system"). The installer now detects a usable systemd via
  `/run/systemd/system`, installs the unit files either way and only skips
  enable/start. `uninstall.sh` had the same problem and aborted before removing
  the program files.
- **Repository name.** The default download location is now
  `loe17/Bonbridge`. `raw.githubusercontent.com` and `codeload.github.com` are
  case sensitive, so the lower-case spelling could 404.
- **Download robustness.** `install.sh` now tries `codeload.github.com`, then
  `github.com/.../archive`, then falls back to `git clone`, and it resolves
  tags (`--branch v1.0.1`) as well as branches. The extracted directory is
  located by looking for `src/bonbridge` instead of guessing its name.
- Serial ports are no longer listed as usable devices when pySerial is
  missing.
- The recommended POS font is now Font B (`font2`) whenever the printer has
  one, matching the OrderAssist example receipt. Previously a printer whose
  Font A already had 48 columns (TM-m30III, TM-T20III) was recommended with
  Font A.

### Added

- **`docs/de/09-referenzen.md` and `docs/en/09-references.md`**: every piece of
  third-party code, data source and specification with a link, its licence and
  the exact place in the project where it is used - vendored code (zj-58,
  escpos-printer-db), runtime dependencies, the ESC/POS command table with the
  function that implements each command, RAW/JetDirect, mDNS, ENPC, the
  OrderAssist documentation and the related projects that were evaluated.
- Reference blocks in the module docstrings of `escpos.py`, `caps.py`,
  `raw_server.py`, `mdns.py` and the transports, pointing at the specification
  each one implements.
- The recommendation now carries a note that the line width comes from the
  model database and should be reduced by one if the divider still wraps.
- Profile detection reasons are bilingual so they read correctly in the German
  interface.

## [1.0.0] - 2026-08-18

First release under the new name. Complete rewrite of
`OrderAssist-over-Raspberry-Pi-with-Epson-TM-T88V`.

### Added

- **`bonbridge` daemon** written in Python, replacing the CUPS + `socat`
  shell setup.
- **RAW/JetDirect listener on port 9100**, one per printer, bindable to a
  specific IP address so that several print groups can be served from one
  device (POS apps identify printers by IP only).
- **Four transports**: `usb` (libusb/pyusb), `usblp` (`/dev/usb/lp*`),
  `serial` (RS-232, USB-serial, CDC-ACM) and `network` (TCP 9100).
  The libusb transport makes printers work that never create
  `/dev/usb/lp0` - such as the Epson TM-m30 family and the TM-M244A.
- **Bidirectional communication** with the printer, so `DLE EOT` status
  (paper end, paper near end, cover open, cutter error) is available and
  shown as a traffic light.
- **Job queue with spooling and retry.** A job that cannot be delivered is
  written to `/var/lib/bonbridge/spool/` and retried; spooled jobs survive a
  service restart.
- **Capability engine**: identification from USB descriptors, the IEEE-1284
  device ID and the ESC/POS `GS I` printer ID, matched against the bundled
  escpos-printer-db plus this project's own profiles. Every feature can be
  overridden from the web interface.
- **POS setting recommendations.** Font, character set and line width are
  derived from the printer profile instead of being found by trial and error
  (TM-T88V → `font2`, `cp1252`, 56 columns).
- **Web interface** (no build step, no external assets, German and English)
  with overview, printer management, feature matrix, diagnostics, an
  integration guide and system settings.
- **REST API** for every function the web interface offers, plus a
  `/healthz` endpoint and a downloadable plain-text support report.
- **Test pages** modelled on the OrderAssist test receipt: character ruler,
  special characters, alignment, table, divider and QR code.
- **Active probes** for cutter, cash drawer, buzzer and paper feed.
- **One-command installer** for Raspberry Pi Zero 2 W, Pi 3/4/5 and x86-64,
  with an uninstaller, a systemd unit, a udev rule and an IP-alias unit for
  multi-printer setups.
- **`bonbridge` command line tool** (`scan`, `report`, `test`, `run`).
- **Optional CUPS module.** Its queue prints *through* BonBridge instead of
  competing for the device, and `/etc/cups/cupsd.conf` is never modified.
- **Vendored dependencies**: zj-58 (BSD-2-Clause) and escpos-printer-db
  (CC BY 4.0) live in `vendor/`, so installation never depends on a
  third-party repository staying online.
- **Documentation in German and English** (hardware, wiring diagrams,
  printer configuration, POS integration, web interface, diagnostics, print
  groups, architecture) including SVG diagrams.
- **CI and release automation** via GitHub Actions: byte-compile and
  end-to-end test against a mock printer on Python 3.9/3.11/3.13, shellcheck,
  an installer smoke test in a Debian container, and tagged releases with an
  offline archive.
- **Mock printer** (`tests/mock_printer.py`) and a 28-check end-to-end test
  that runs without any hardware.
- Experimental Epson ENPC discovery responder (UDP 3289), disabled by
  default.

### Fixed (compared to the previous project)

- `install.sh` began with a stray `bash` line before the shebang, a leftover
  from a copied markdown code block.
- `README.md` ended inside an unterminated code fence.
- `socat -u` was write-only, so no printer status could ever be read and
  failed jobs disappeared silently.
- CUPS and `socat` both wrote to `/dev/usb/lp0` with no locking, so
  concurrent jobs could interleave.
- The installer aborted when `/dev/usb/lp0` did not exist, which excluded
  every printer that does not use the USB printer class.
- `/etc/cups/cupsd.conf` was overwritten wholesale with `DefaultAuthType
  None` and `Allow all`, exposing CUPS administration to the whole LAN and
  discarding any existing configuration.
- `IdleExitTimeout 60` combined with a disabled `cups.socket` risked cupsd
  exiting after idling with nothing to wake it up.
- `lpadmin -m raw`, `accept` and `netstat` are deprecated or absent on
  current Debian releases; their failures were swallowed by `|| true`.
- Installation required a compiler and a live clone of
  `github.com/klirichek/zj-58`.

### Notes

- The repository was renamed from
  `OrderAssist-over-Raspberry-Pi-with-Epson-TM-T88V` to `bonbridge`. GitHub
  keeps redirecting the old name, so existing links and clones keep working.
- See `MIGRATION.md` for upgrading an existing Raspberry Pi.

[1.1.1]: https://github.com/loe17/Bonbridge/releases/tag/v1.1.1
[1.1.0]: https://github.com/loe17/Bonbridge/releases/tag/v1.1.0
[1.0.1]: https://github.com/loe17/Bonbridge/releases/tag/v1.0.1
[1.0.0]: https://github.com/loe17/Bonbridge/releases/tag/v1.0.0
