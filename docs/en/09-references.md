# References: third-party code and sources

This page lists **every piece of third-party code, every data source and every
specification** BonBridge builds on - with a link, its licence and the place in
the project where it is used.

The machine-readable short version lives in [`NOTICE`](../../NOTICE).

---

## 1. Bundled third-party code (`vendor/`)

Both components are **copied into the repository** on purpose: installation
must keep working even if one of these projects disappears from GitHub. Each
directory contains a `VENDORED_COMMIT` file recording the upstream revision the
copy was taken from.

### 1.1 zj-58 - CUPS filter for ESC/POS printers

| | |
|---|---|
| **Project** | [klirichek/zj-58](https://github.com/klirichek/zj-58) |
| **Author** | Aleksey N. Vinogradov |
| **Licence** | [BSD 2-Clause](https://github.com/klirichek/zj-58/blob/master/LICENSE) - redistribution permitted |
| **Located at** | [`vendor/zj-58/`](../../vendor/zj-58/) |
| **Used by** | the **optional** CUPS module: [`install.sh`](../../install.sh) (`--with-cups`) and [`packaging/cups/setup-cups.sh`](../../packaging/cups/setup-cups.sh) |
| **What for** | Rasterises CUPS print data (ordinary documents, operating-system test pages) into ESC/POS bitmaps. Ships the PPDs `zj58.ppd` (58 mm) and `zj80.ppd` (80 mm). |
| **Not needed for** | OrderAssist. POS printing goes over RAW/9100 entirely without CUPS and without zj-58. |

Files taken over:

| File | Purpose |
|---|---|
| [`vendor/zj-58/rastertozj.c`](../../vendor/zj-58/rastertozj.c) | the CUPS filter itself |
| [`vendor/zj-58/zj58.ppd`](../../vendor/zj-58/zj58.ppd), [`zj80.ppd`](../../vendor/zj-58/zj80.ppd) | 58 / 80 mm printer descriptions |
| [`vendor/zj-58/zjdrv.drv`](../../vendor/zj-58/zjdrv.drv) | source the PPDs are generated from |
| [`vendor/zj-58/CMakeLists.txt`](../../vendor/zj-58/CMakeLists.txt) | build |
| [`vendor/zj-58/LICENSE`](../../vendor/zj-58/LICENSE) | the original's unmodified licence |

> The previous project **cloned and compiled zj-58 from GitHub at install
> time**. That is gone: the code lives in the repository and is only built if
> you actually want CUPS.

### 1.2 escpos-printer-db - printer capability database

| | |
|---|---|
| **Project** | [receipt-print-hq/escpos-printer-db](https://github.com/receipt-print-hq/escpos-printer-db) |
| **Browsable version** | <https://mike42.me/escpos-printer-db/> |
| **Licence** | [Creative Commons Attribution 4.0](https://github.com/receipt-print-hq/escpos-printer-db/blob/master/LICENSE.md) - attribution given here and in [`NOTICE`](../../NOTICE) |
| **Located at** | [`vendor/escpos-printer-db/capabilities.json`](../../vendor/escpos-printer-db/capabilities.json) |
| **Used by** | [`src/bonbridge/caps.py`](../../src/bonbridge/caps.py) → `load_capability_db()`, `get_profile()`, `profile_features()`, `recommend_pos_settings()` |
| **What for** | Per model: fonts and characters per line, paper width and resolution, supported code pages, and the feature flags (cutter, cash drawer, barcode, QR, PDF417, graphics). These drive the feature matrix and the **recommended POS settings**. |
| **Size** | about 50 models, among them `TM-T88V`, `TM-m30III`, `TM-T20III`, `ITPP047` (Munbyn), `ZJ-5870` |

Concrete example: the reason BonBridge suggests `font2` / `cp1252` /
`56 columns` for a TM-T88V is the `TM-T88V` entry in this database
(`fonts."1".columns = 56`, `codePages."16" = CP1252`).

Additions of our own live as YAML under
[`src/bonbridge/profiles/`](../../src/bonbridge/profiles/) - they add
identification hints (USB product strings) and setup notes without modifying
the original data.

---

## 2. Runtime dependencies (not bundled, installed from the distribution)

| Package | Project | Licence | Used in |
|---|---|---|---|
| `python3` | [python.org](https://www.python.org/) | PSF | everywhere |
| `python3-usb` (PyUSB) | [pyusb/pyusb](https://github.com/pyusb/pyusb) | BSD-3-Clause | [`transports/usb_libusb.py`](../../src/bonbridge/transports/usb_libusb.py) |
| `python3-serial` (pySerial) | [pyserial/pyserial](https://github.com/pyserial/pyserial) | BSD-3-Clause | [`transports/serial_port.py`](../../src/bonbridge/transports/serial_port.py) |
| `python3-yaml` (PyYAML) | [yaml/pyyaml](https://github.com/yaml/pyyaml) | MIT | [`config.py`](../../src/bonbridge/config.py), [`caps.py`](../../src/bonbridge/caps.py) |
| `libusb-1.0` | [libusb/libusb](https://github.com/libusb/libusb) | LGPL-2.1-or-later | underneath PyUSB |
| `avahi-daemon` | [avahi.org](https://www.avahi.org/) | LGPL-2.1-or-later | [`mdns.py`](../../src/bonbridge/mdns.py) (optional) |
| `python3-zeroconf` | [python-zeroconf/python-zeroconf](https://github.com/python-zeroconf/python-zeroconf) | LGPL-2.1 | [`mdns.py`](../../src/bonbridge/mdns.py) (optional, only if installed) |
| `cups` | [OpenPrinting CUPS](https://github.com/OpenPrinting/cups) | Apache-2.0 | optional CUPS module |
| `iproute2` | [iproute2](https://git.kernel.org/pub/scm/network/iproute2/iproute2.git) | GPL-2.0 | [`sysinfo.py`](../../src/bonbridge/sysinfo.py), [`packaging/bin/bonbridge-ip`](../../packaging/bin/bonbridge-ip) |

Deliberately **not** used: web framework, ORM, build toolchain, npm. The web
server is the standard library
([`http.server`](https://docs.python.org/3/library/http.server.html)) and the
interface is a single HTML file with plain JavaScript.

---

## 3. Protocols and specifications

### ESC/POS (Seiko Epson)

| Source | What it is used for |
|---|---|
| [ESC/POS Command Reference (Epson)](https://download4.epson.biz/sec_pubs/pos/reference_en/escpos/index.html) | the basis of [`escpos.py`](../../src/bonbridge/escpos.py) |
| [TM-T88V: supported commands](https://download4.epson.biz/sec_pubs/pos/reference_en/escpos/tmt88v.html) | verifying which commands the TM-T88V really implements |
| [TM-T88V Technical Reference Guide (PDF)](https://files.support.epson.com/pdf/pos/bulk/tm-t88v_trg_en_revf.pdf) | DIP switches, memory switches, interface boards → [03-printer-setup.md](03-printer-setup.md) |
| [TM-T88VI Technical Reference Guide (PDF)](https://files.support.epson.com/pdf/pos/bulk/tm-t88vi_trg_en_revg.pdf) | cross-check against newer models |

Commands actually used and where they live
([`src/bonbridge/escpos.py`](../../src/bonbridge/escpos.py)):

| Command | Bytes | Function in the code | Purpose |
|---|---|---|---|
| `ESC @` | `1B 40` | `INIT` | reset the printer |
| `ESC t n` | `1B 74 n` | `select_codepage()` | character set (cp1252 = 16) |
| `ESC M n` | `1B 4D n` | `select_font()` | Font A / Font B |
| `ESC a n` | `1B 61 n` | `align()` | alignment |
| `ESC d n` | `1B 64 n` | `feed()` | paper feed |
| `ESC p m t1 t2` | `1B 70 …` | `drawer_pulse()` | cash drawer |
| `ESC ( A` | `1B 28 41 …` | `buzzer()` | buzzer |
| `GS V m n` | `1D 56 …` | `cut()` | paper cut |
| `GS ( k` | `1D 28 6B …` | `qrcode()` | QR code |
| `GS k 4` | `1D 6B 04 …` | `barcode_code39()` | CODE39 barcode |
| `GS I n` | `1D 49 n` | `GS_I_MODEL/TYPE/ROM` | printer identification |
| `GS r n` | `1D 72 n` | `GS_R_PAPER/DRAWER` | paper and drawer status |
| `GS a n` | `1D 61 n` | `enable_asb()` | Automatic Status Back |
| `DLE EOT n` | `10 04 n` | `STATUS_DECODERS` | real-time status (paper, cover, errors) |

The status bits are decoded in `decode_printer_status()`,
`decode_offline_status()`, `decode_error_status()` and
`decode_paper_status()`.

### RAW / JetDirect (port 9100)

Not a formal standard but the HP-introduced practice of "open TCP 9100, push
bytes, printer prints". Implemented in
[`raw_server.py`](../../src/bonbridge/raw_server.py). Related references:

* [RFC 1179 - Line Printer Daemon Protocol](https://datatracker.ietf.org/doc/html/rfc1179) (LPD, the older alternative)
* [CUPS `socket` backend](https://www.cups.org/doc/network.html) - the counterpart when a Linux machine prints to BonBridge

### mDNS / DNS-SD

* [RFC 6762 - Multicast DNS](https://datatracker.ietf.org/doc/html/rfc6762)
* [RFC 6763 - DNS-Based Service Discovery](https://datatracker.ietf.org/doc/html/rfc6763)
* Service types `_pdl-datastream._tcp` (RAW printing) and `_http._tcp`
  ([IANA registry](https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml))

Implemented in [`mdns.py`](../../src/bonbridge/mdns.py).

### Discoverability: which protocols an Epson network board speaks

The authoritative primary source is the technical reference of the TM-T88V's
interface board. It lists every protocol a real device answers - and therefore
the list BonBridge reproduces:

* [Epson UB-E04 Technical Reference Guide](https://files.support.epson.com/pdf/ube04_/ube04_trg.pdf) - LPR (515), RAW (9100), SNMP v1 (161, community `public`), ENPC (3289, packet types Probe/Initialize/Query/Setup/Notify), mDNS, HTTP

### ENPC (Epson network discovery, UDP 3289) - partly reconstructed

Epson does **not** publish the reply format. The frame layout in
[`discovery.py`](../../src/bonbridge/discovery.py) rests on public third-party
analysis, which is why BonBridge can send several reply variants and logs every
request with a hexdump instead of presenting a guess as fact:

* [wes4m: "Reverse Engineering Thermal Printers"](https://wes4m.io/posts/epson_rev/) - frame layout `EPSONQ`/`EPSONq`, `EPSONC`/`EPSONc`, function numbers
* [mike42/escpos-php issue #923: "Need help with ENPC protocol 3289"](https://github.com/mike42/escpos-php/issues/923) - the observed 16-byte ePOS SDK search packet
* [Epson ePOS SDK: `Discovery.start`](https://download4.epson.biz/sec_pubs/pos/reference_en/epos_and/ref_epos_sdk_and_en_discoveryclass_start.html) - the official client side

### SNMP (UDP 161)

Fully and publicly specified; the implementation in
[`snmp.py`](../../src/bonbridge/snmp.py) encodes BER by hand so that `pysnmp`
is not needed:

* [RFC 1157 - Simple Network Management Protocol (v1)](https://datatracker.ietf.org/doc/html/rfc1157)
* [RFC 1213 - MIB-II](https://datatracker.ietf.org/doc/html/rfc1213) (`sysDescr`, `sysName`, `sysObjectID`)
* [RFC 2790 - Host Resources MIB](https://datatracker.ietf.org/doc/html/rfc2790) (`hrDeviceDescr`, `hrPrinterStatus`)
* [RFC 3805 - Printer MIB v2](https://datatracker.ietf.org/doc/html/rfc3805) (`prtGeneralPrinterName`)
* Epson's IANA enterprise number is **1248** -> `sysObjectID = 1.3.6.1.4.1.1248`

### IEEE 1284 device ID

Read from `/sys/class/usbmisc/lp*/device/ieee1284_id`
([`transports/usblp.py`](../../src/bonbridge/transports/usblp.py)), giving
`MFG:`/`MDL:`/`SN:` for model identification.
Reference: [Linux `usblp` driver](https://www.kernel.org/doc/html/latest/usb/index.html)

---

## 4. POS system documentation

| Source | What came from it |
|---|---|
| [OrderAssist - Drucker](https://doku.order-assist.de/docs/handbuch/drucker/) | printers are added **by IP only**, the port is fixed at 9100; the automatic search finds EPSON devices only; the font / character set / line width fields; the layout of the test page |
| [OrderAssist - Empfohlene Hardware](https://doku.order-assist.de/docs/empfohlene-hardware) | **USB and serial are not supported** - the reason this project exists |
| [OrderAssist - Ausdruckgruppen](https://doku.order-assist.de/docs/handbuch/ausdruckgruppen/) | why several printers need several IP addresses → [07-print-groups.md](07-print-groups.md) |

The BonBridge test page in `escpos.test_page()` deliberately mirrors the
OrderAssist test page (character ruler, special characters, alignment, table,
divider, QR) so the two can be compared directly.

---

## 5. Predecessor and related projects

Not taken over as code, but evaluated as a template, a cross-check or an
alternative:

| Project | What came from it |
|---|---|
| [loe17/OrderAssist-over-Raspberry-Pi-with-Epson-TM-T88V](https://github.com/loe17/OrderAssist-over-Raspberry-Pi-with-Epson-TM-T88V) | the direct predecessor of this repository (CUPS + zj-58 + socat). The insight "RAW on 9100, not IPP" comes from there. Migration: [`MIGRATION.md`](../../MIGRATION.md) |
| [plinth666/epsonsimplecups](https://github.com/plinth666/epsonsimplecups) | an alternative, very lean CUPS driver for the Epson TM-T20 - cross-check against zj-58 |
| [trandi/esp32-thermal_printer](https://github.com/trandi/esp32-thermal_printer) | ESP32 driving a TM-T88 over serial - the basis of the ESP32 evaluation in [01-hardware.md](01-hardware.md) |
| [touchgadget/esp32-usb-host-demos](https://github.com/touchgadget/esp32-usb-host-demos) | experimental USB host printer driver for ESP32-S2/S3 - shows the route is technically possible but not production ready |
| [Aaron Chambers: T88V Raspberry Pi mount (Printables)](https://www.printables.com/model/1340272-t88v-raspberry-pi-full-size-mount) | 3D printable mount for Pi + TM-T88V, mentioned in the bill of materials |
| [Elektronik-Kompendium: print server with CUPS and AirPrint](https://www.elektronik-kompendium.de/sites/raspberry-pi/2007081.htm) | reference for the classic CUPS approach |
| [German Raspberry Pi forum: TM-T88VI over CUPS](https://forum-raspberrypi.de/forum/thread/60662-epson-tm-t-88vi-mit-cups-ueber-netzwerk-ansteuern/) | field reports on Epson + CUPS |
| [python-escpos](https://github.com/python-escpos/python-escpos) | **no code taken** - but sharing the escpos-printer-db and its profile semantics follows its lead |
| [mike42/escpos-php](https://github.com/mike42/escpos-php) | same, plus the ENPC research |

---

## 6. Licensing in one sentence

BonBridge itself is [MIT licensed](../../LICENSE). The bundled zj-58 code stays
BSD-2-Clause, the bundled model database stays CC BY 4.0. Both licences permit
redistribution inside the repository but require attribution - which is given
in [`NOTICE`](../../NOTICE) and on this page.

ESC/POS is a trademark of Seiko Epson Corporation. BonBridge implements only
the publicly documented command set and is not affiliated with Seiko Epson or
with OrderAssist.
