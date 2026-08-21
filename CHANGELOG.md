# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/), and the
project uses [Semantic Versioning](https://semver.org/).

## [1.3.0] - 2026-08-21

Being found automatically, taken seriously.

### The problem

A printer is never simply "found" or "not found" - only ever over a particular
protocol. BonBridge answered exactly one of them (Epson's undocumented ENPC on
UDP 3289) and was silent on every other, so an app that searches a different
way found nothing, correctly, because there was nothing to find.

The primary source settles what "everything" means: the technical reference of
the TM-T88V's own Ethernet board (UB-E04) lists **LPR on 515, RAW on 9100,
SNMP v1 on 161, ENPC on 3289, mDNS and HTTP**. That is the list a real Epson
device answers, and now the list BonBridge answers.

### Added

- **SNMP v1 responder on UDP 161**, community `public`, exactly as the UB-E04
  does. This is the most common printer discovery of all - sweeping a subnet
  with one query for `sysDescr` - and BonBridge previously ignored it
  completely. Serves the MIB-II system group, the Host Resources MIB
  (`hrDeviceDescr`, `hrPrinterStatus`), the Printer MIB
  (`prtGeneralPrinterName`) and `sysObjectID` under Epson's enterprise arc
  1.3.6.1.4.1.1248. BER is encoded by hand; no new dependency. Verified against
  the real `snmpget`/`snmpwalk` clients, including a `GetNext` walk that
  terminates.
- **LPD/LPR server on TCP 515** (RFC 1179). Answers queue-status probes, and
  since the protocol is small enough to implement properly, actually accepts
  print jobs and forwards them to the printer like a job on 9100.
- **Passive listeners on IPP (631), ePOS-Device (8008) and SSDP (1900).** These
  never answer - a half-implemented IPP reply would be worse than silence -
  but they record who knocked, which is the missing information.
- **One shared probe log across every protocol**, with sender, hexdump and a
  summary. One press of "search for printers" in the app now answers the
  decisive question outright: *which protocol did the app actually speak?*
  The diagnostics page shows all protocols side by side with the number of
  probes each has seen.
- **The announced manufacturer and model are now settable.** Apps that search
  specifically for Epson printers filter on exactly these strings, so they
  decide whether the device appears in the list at all. `auto` announces the
  model that was actually detected on the USB port (e.g. TM-T88V) and only
  falls back to a default when nothing was detected.
- **Selectable ENPC reply shape** (`echo` / `epson` / `both`, default `both`).
  Epson does not publish the reply payload; rather than presenting one guess as
  fact, BonBridge can send a mirrored and a structured variant in quick
  succession and log both.

### Changed

- **ENPC now answers every `EPSON<uppercase letter>` request**, not just
  `EPSONQ` and `EPSONC`. The UB-E04 reference lists the packet types Probe,
  Initialize, Query, Setup and Notify, so hard-coding two of them was a guess
  that could only be wrong. The reply carries the matching lower-case letter.
- **mDNS announces `_printer._tcp` as well as `_pdl-datastream._tcp`**, with an
  `rp` record. Clients that only browse the classic printer type could not see
  the device before.
- Discovery settings are applied by restarting the listeners immediately, so
  saving them means something without a service restart.
- The diagnostics page reports discovery as a protocol table rather than a
  single ENPC counter.

### Notes

The ENPC reply payload is still not verifiable without an original device.
That is why the emphasis here is on *measurement*: three protocols that are
fully specified (SNMP, LPD, mDNS) now answer correctly, and for the one that is
not, the probe log makes the next step concrete instead of speculative.

## [1.2.0] - 2026-08-20

### Added

- **Software updates, three ways in, one installation path.** `bonbridge update`
  on the console checks GitHub, shows the release notes, asks once and installs
  with live output. The web interface does the same with a confirmation dialog
  and the installer output streamed into the page. For devices with no internet
  access, a release archive can be uploaded and installed instead. All three end
  in the repository's own `install.sh` - there is no second installation
  mechanism that could drift apart from the first.
  - Only published releases/tags are offered, never the moving `main` branch.
    A pushed git tag is enough: when a repository has no GitHub *release*
    entries, the tag list is used instead.
  - The previous installation is packed into `/var/lib/bonbridge/backups/`
    before anything is replaced. `bonbridge update --rollback` puts it back.
  - Uploaded archives are unpacked and validated *before* installing: they must
    contain `install.sh`, `src/bonbridge/` and `VERSION`, and no archive member
    may escape the target directory.
  - `update.allow_web` (default on) is a real security switch. The web interface
    has no password, so installing software through it is a genuine decision;
    turning it off leaves `sudo bonbridge update` over SSH as the only way in.
  - Under systemd the installer runs as its own transient unit, because
    `systemctl restart bonbridge` would otherwise kill the process doing the
    installing - it is a child of the service being restarted.
- **Network watchdog with fault receipts.** When the device loses its network
  connection the POS application simply stops printing, and the usual diagnosis
  is "the printer is broken". The printer is fine and still reachable over USB,
  so it now prints a slip saying what actually happened and what to check - at
  start-up without a network, on an outage, and again when the connection
  returns (carrying the possibly changed IP address).
  - Link state is read straight from `/sys/class/net`, with no helper process.
  - A changed state must survive two consecutive checks by default, so a brief
    Wi-Fi roam does not produce a slip.
  - Nothing is printed when no printer is connected: a spooled fault slip that
    surfaces days later, out of context, helps nobody.
  - Interval, on/off and the optional gateway ping are configurable in the web
    interface; which printer reports an outage is a per-printer option.
- **Printing images from the web interface**, with a preview that is not a
  simulation: the device rasterises the file and sends back exactly the bitmap
  it would print, so a logo that turns into a black block after thresholding is
  visible before it costs paper. PNG, JPG, BMP, GIF and WebP; dithering or a
  hard threshold, scaling and inversion. PDF is refused with an explanation
  rather than a stack trace.
- New documentation chapter **10 - Updates, network watchdog, maintenance** in
  German and English.

### Fixed

- **Collapsed sections no longer spring open again.** The overview re-renders
  every five seconds, and every re-render rebuilt the health panels in their
  default state - so collapsing one lasted at most five seconds. Open/closed
  state is now remembered per block and survives both the refresh and a page
  reload.
- **The automatic refresh no longer discards what you are typing.** On the
  Features tab, changing a dropdown and not saving within five seconds silently
  lost the change. The refresh now pauses for a tab that holds unsaved edits.
- **Printers were identified as generic even when the model was known.** Two
  causes, both fixed:
  - The IEEE-1284 device ID (`MFG:EPSON;MDL:TM-T88V;...`) was collected but
    never matched against. For a printer reached through `/dev/usb/lpN` that is
    often the *only* place the model name appears, so those connections always
    fell back to the generic profile. The identification now also uses the
    IEEE-1284 ID and any readable `GS I` reply.
  - With libusb, the descriptor strings were read *after* the interface had been
    claimed, where a second control transfer frequently fails and silently
    returned empty strings. They are now read before the claim.
  - When identification really is impossible, that is now said out loud: the
    printer's status reports the generic profile as a warning and lists which
    identifiers could be read at all, instead of quietly guessing.
- Long diagnostics output (command output, status and identity JSON, discovery
  hexdumps) is collapsible instead of filling the page.

### Changed

- `python3-pil` is installed by default (needed for image printing). If it
  cannot be installed the rest still installs and the interface says how to add
  it later.
- Request body limit raised from 8 MiB to 48 MiB for uploads.

## [1.1.2] - 2026-08-19

Support for very old boards - a Raspberry Pi 1 or the original Pi Zero (ARMv6,
one core at 700 MHz, 256-512 MB RAM) now has documented, tested expectations,
and the web interface no longer creates avoidable background load on them.

### Added

- **Raspberry Pi 1 / Pi Zero / Pi 2 documented** in the hardware chapter (DE and
  EN): which image to flash (32-bit only - the 64-bit image does not boot on
  ARMv6), how the LAN socket on the Model B/B+ behaves (it hangs off the same
  USB controller as the printer, which is irrelevant at receipt sizes), why the
  printer's own 24 V supply keeps the weak polyfuses out of the picture, what to
  expect in terms of speed, and until when Debian carries these boards.
- **The installer checks the Python version** and says so, instead of failing
  later with an import error. 3.9 or newer is required.
- **The installer warns before adding CUPS on a board with under ~700 MB RAM.**
  CUPS is optional and BonBridge does not need it.
- **`ruff.toml`** pins the lint rule set and `target-version = "py39"`, and the
  CI lint job is now a real gate instead of `|| true`. Without the pin, a new
  Ruff release started demanding PEP 585 syntax that Python 3.9 on Raspberry Pi
  OS Bullseye does not understand.

### Changed

- **Readings that fork a helper process are cached.** `/api/overview` is polled
  every five seconds by every open browser tab, and it read the IP addresses via
  `ip` and the throttling state via `vcgencmd` on every single request. Both are
  now cached (15 s and 30 s); the board model and `/etc/os-release` are cached
  for longer. On a Pi 1 this removes two fork+exec cycles every five seconds per
  tab; on faster boards it is simply less pointless work.

### Fixed

- Two source lines exceeded the line limit that the new lint gate enforces; one
  of them was a genuinely unreadable nested expression.

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

[1.3.0]: https://github.com/loe17/Bonbridge/releases/tag/v1.3.0
[1.2.0]: https://github.com/loe17/Bonbridge/releases/tag/v1.2.0
[1.1.2]: https://github.com/loe17/Bonbridge/releases/tag/v1.1.2
[1.1.1]: https://github.com/loe17/Bonbridge/releases/tag/v1.1.1
[1.1.0]: https://github.com/loe17/Bonbridge/releases/tag/v1.1.0
[1.0.1]: https://github.com/loe17/Bonbridge/releases/tag/v1.0.1
[1.0.0]: https://github.com/loe17/Bonbridge/releases/tag/v1.0.0
