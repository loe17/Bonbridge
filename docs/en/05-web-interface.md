# Web interface

Reachable at `http://<ip>:8080/` and - when Avahi is running - at
`http://<hostname>.local:8080/`.

The interface is **deliberately unauthenticated** and intended for the local
network. Do not forward port 8080 to the internet. The language (DE/EN) is
switchable in the top right corner.

## Overview

Shows a traffic light per printer:

| Colour | Meaning |
|---|---|
| 🟢 green | Ready |
| 🟡 yellow | Warning, e.g. paper near end |
| 🔴 red | Error: paper end, cover open, cutter error, or not connected |
| ⚪ grey | Status unknown (transport without a return channel) |

Plus: the address for the POS application (click to copy), connection,
detected model, job counters, last job, last error, and the state of the
network listener.

The page refreshes itself every five seconds.

## Printers

Management of printer entries.

* **Scan for devices** - lists all USB, `usblp` and serial devices that could
  be receipt printers. *Use* assigns a device to a printer.
* **Name** - free text, appears on test prints and in the support report.
* **IP address for port 9100** (`bind`) - `0.0.0.0` means "every address of
  this device". For several print groups each printer gets its own IP here,
  see [07-print-groups.md](07-print-groups.md).
* **Connection** - `auto`, `usb`, `usblp`, `serial` or `network`. `auto` picks
  the most plausible local device at every start.
* **Printer profile** - `automatic` or a specific model from the bundled
  database.
* **Options** - cut after every job, open drawer after every job, `ESC @`
  before every job, status polling interval, paper feed.

Changes take effect immediately; the affected listeners restart.

## Features

The feature matrix per printer. Each row shows:

* **detected** - what profile and live query determined
* **setting** - `automatic` / `on (forced)` / `off (forced)`
* **effective** - what BonBridge actually uses

Detected features are: paper cutter, cash drawer, buzzer, barcodes, QR codes,
PDF417, raster graphics, NV logo and status read-back.

**Why override?** The model database is a collection of community
observations. If your unit is listed as "has a cutter" but does not have one
(series variant, cutter removed), switch the feature off here - BonBridge then
stops sending cut commands.

Below that are the **recommended POS settings** and the **active tests**:

| Test | Effect |
|---|---|
| Test cutter | Paper feed + partial cut |
| Open cash drawer | `ESC p` - the drawer should pop open |
| Buzzer | `ESC ( A` - only on units with a buzzer |
| Feed paper | Four lines |
| Feature test page | Bold, double size, barcode, QR |

These tests consume paper and therefore never run automatically.

## Diagnostics

* **Recent print jobs** - number, source (IP of the POS device), size,
  timestamp and a readable preview of the data. This answers the question
  *did the job arrive at all?*
* **Send raw data** - text or hex bytes straight to the printer, e.g. `1B 40`
  for `ESC @` (reset). For troubleshooting and memory switches.
* **Clear spool** - discards spooled jobs that should not be printed any more.
* **Status / Identity** - the raw answers to `DLE EOT` and `GS I`.
* **System output** - `lsusb`, `/dev/usb/`, `ss -tlnp`, `ip addr`,
  `dmesg | tail`, kernel modules, service status.
* **Download support report** - a text file containing all of the above. This
  is the file to attach to a support request.

## Integration

A ready-made, copy-and-paste setup guide - see
[04-pos-integration.md](04-pos-integration.md). Contains the clickable IP, the
recommended print settings, a numbered step list and example commands for
CUPS, Windows, macOS and the command line.

## System

* Device label, web interface port, RAW port
* mDNS/Bonjour announcement on/off
* Answer Epson discovery probes (ENPC) - **experimental**, see
  [06-diagnostics.md](06-diagnostics.md)
* System information: model, OS, kernel, architecture, Python, uptime, free
  disk space
* Links to the documentation in the selected language

## REST API

The interface uses nothing but this API, so a script or a monitoring system
can use it too.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/overview` | Overall status |
| GET | `/healthz` | Liveness probe for monitoring |
| GET/PUT | `/api/config` | Read/change configuration |
| GET/POST | `/api/printers` | List/create printers |
| GET/PATCH/DELETE | `/api/printers/<id>` | Read/update/delete a printer |
| POST | `/api/printers/<id>/test` | Test print (`kind`: `standard`, `features`, `minimal`) |
| POST | `/api/printers/<id>/probe` | `what`: `cut`, `drawer`, `buzzer`, `feed` |
| POST | `/api/printers/<id>/raw` | `{"hex": "1B40"}` or `{"text": "..."}` |
| POST | `/api/printers/<id>/refresh` | Re-read status |
| POST | `/api/printers/<id>/redetect` | Rebuild connection and detection |
| GET | `/api/printers/<id>/integration` | Values for the POS application |
| GET | `/api/scan` | Scan for devices |
| GET | `/api/profiles` | Available printer profiles |
| GET | `/api/diagnostics` | System info + command output |
| GET | `/api/report` | Support report as plain text |
| POST | `/api/restart` | Restart printers and listeners |

Example:

```bash
curl -s http://192.168.1.50:8080/api/overview | python3 -m json.tool
curl -s -X POST http://192.168.1.50:8080/api/printers/printer1/test \
     -H 'Content-Type: application/json' -d '{"kind":"standard"}'
```
