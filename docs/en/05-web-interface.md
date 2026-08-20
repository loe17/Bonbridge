# Web interface

Reachable at **`http://<ip>:8080/`**.

> The name `<hostname>.local` is also announced over mDNS. That works on macOS,
> iOS, Android and most Linux desktops, but on **Windows only with Bonjour
> installed**. Rely on the IP address - it works everywhere. The name is a
> convenience, not a requirement.

The interface is **deliberately unauthenticated** and intended for the local
network. Do not forward port 8080 to the internet. The language (DE/EN) is
switchable in the top right corner.

## Overview

Shows the **device status** first and a traffic light per printer below it.

Under every traffic light there is an expandable **"Why? Show all individual
checks"**. It lists each check with its own level and an explanation of what to
do - under-voltage, CPU temperature, free disk space, missing Python modules,
the state of the network listener, paper, cover, spool. There is no unexplained
yellow light any more.

The light means:

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
* **IP address for port 9100** (`bind`) - see the dedicated section below. In
  short: with one printer leave it at `0.0.0.0`.
* **Connection** - `auto`, `usb`, `usblp`, `serial` or `network`. `auto` picks
  the most plausible local device at every start.
* **Printer profile** - `automatic` or a specific model from the bundled
  database.
* **Options** - see the table below.

Changes take effect immediately; the affected listeners restart. Every input
field carries an explanation that appears on hover.

### Per-printer options

| Option | Default | Effect |
|---|---|---|
| **Print a status slip on start-up** | **on** | Prints a slip with the IP address, port and POS settings right after power-up. The device has no screen - the slip is the fastest route to the IP address. The setting lives in `config.yaml` and survives a power cut. |
| **Warn when the paper runs low** | off | Prints a **one-off** notice as soon as the printer reports "paper near end". It is printed again only after new paper has been detected. This state also survives a reboot. |
| Cut after every job | off | Only enable when the POS application does not cut itself, otherwise it cuts twice. |
| Open the cash drawer after every job | off | Usually undesirable for a kitchen printer. |
| Reset (`ESC @`) before every job | off | Helps when a previous job leaves the font size or alignment changed. |
| Status polling | on | Without it the traffic light stays grey. |
| Polling interval | 10 s | Smaller values load the printer for nothing. |
| Feed lines after job | 0 | Extra blank lines before the cut. |

### "IP address for port 9100" - what is it for?

This field decides **which IP address of this device** the printer port 9100 is
bound to.

**`0.0.0.0` (default) = every address of the device.** The POS application then
reaches the printer on any IP the Pi has - over Ethernet, over Wi-Fi, and still
after the address changes via DHCP. **With a single printer this is always the
right setting and you never have to touch it.**

There is exactly one case for a **fixed IP**: **several printers on this one
device**. The reason lies in the POS system, not in BonBridge - OrderAssist (and
most others) identify a printer **by IP address only**, the port is fixed at
9100 and cannot be changed in the app. Two printers behind the same IP would be
the same printer to the app.

The solution: give the device a second (third, ...) IP address and let each
printer listen only on its own:

```
Pi 4, one network interface, two USB printers
  192.168.1.50   web interface  (main IP of the device)
  192.168.1.51   kitchen printer -> port 9100
  192.168.1.52   bar printer     -> port 9100
```

Important: the extra IP has to exist **on the device** first, otherwise the
listener cannot start (the overview then shows a red network listener with
exactly that reason). How to create it is in
[07-print-groups.md](07-print-groups.md).

Other sensible reasons for a fixed binding:

* **Serve one network only:** if the device is on Ethernet and Wi-Fi at the same
  time and should only print over one of them, enter that interface's address.
* **Hardening:** with a fixed binding the printer accepts no jobs from the
  device's other networks.

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

## Print

A full receipt editor with a **live preview**. The receipt is assembled on the
left and appears on the right exactly as it will look on paper - in the real
line width of the detected printer.

| Field | Meaning |
|---|---|
| Printer | Which printer the receipt goes to |
| Heading | Large, bold line at the top (optional) |
| Content | One line here = one line on the receipt |
| Footer | Small, centred text at the end |
| QR code | Printed as a QR at the bottom (optional) |
| Cut at the end | Only effective if the printer has a cutter |
| Open the cash drawer | Fires the pulse after printing |

Two shortcuts in the content field:

* A line containing only `---` becomes a **divider**.
* `Text | value` puts the value **flush right** - exactly what price lines want:

  ```
  2x Cola 0.4l | 7.00
  1x Fries     | 3.50
  ---
  Total        | 15.40
  ```

The preview comes out of the same function that produces the print data - what
you see is what gets printed. If the printer cannot do something (no cutter, no
QR code) that is stated below the preview and the command is skipped instead of
producing an error.

What it is for: test receipts without a POS system, labels, handover notes,
end-of-day notes - and above all for checking line width and character set
before configuring the POS application.

### Printing an image

The **Text | Image** switch prints PNG, JPG, BMP, GIF and WebP files. The
preview shows the actual dot pattern, not an approximation. PDF is not
supported. Details in [10-updates.md](10-updates.md).

## Diagnostics

* **Recent print jobs** - number, source (IP of the POS device), size,
  timestamp and a readable preview of the data. This answers the question
  *did the job arrive at all?*
* **Send raw data** - text or hex bytes straight to the printer, e.g. `1B 40`
  for `ESC @` (reset). For troubleshooting and memory switches.
* **Clear spool** - discards spooled jobs that should not be printed any more.
* **Status / Identity** - the raw answers to `DLE EOT` and `GS I`.
* **All checks** - every health check of the device and the printers with its
  reason. This answers "why is there a warning?".
* **Automatic printer search** - whether mDNS and the Epson discovery responder
  are running and, most importantly, **which search requests actually arrived**,
  each with a hexdump. See [06-diagnostics.md](06-diagnostics.md).
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
* Answer the Epson printer search (ENPC, UDP 3289) - on by default, see
  [06-diagnostics.md](06-diagnostics.md)
* Log search requests - lets you verify whether the POS app searches at all
* System information: model, OS, kernel, architecture, Python, uptime, free
  disk space
* **Network watchdog** - state of every interface, check interval and whether a
  notice is printed on an outage (see [10-updates.md](10-updates.md))
* **Updates** - installed and available version, installation with console
  output, file upload for devices without internet, backups
  (see [10-updates.md](10-updates.md))
* Links to the documentation in the selected language

### Collapsed sections stay collapsed

Expanded or collapsed blocks (individual checks, hexdumps, command output) stay
the way you left them - across the automatic refresh every five seconds and
across a page reload. The automatic refresh also pauses while a field holds
unsaved changes, because otherwise it would overwrite them.

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
| GET | `/api/health` | All individual checks with reasons |
| GET | `/api/discovery` | State and log of the automatic search |
| POST | `/api/discovery/clear` | Clear the probe log |
| POST | `/api/printers/<id>/compose` | Build a receipt: `{"spec": …, "print": false}` returns the preview |
| POST | `/api/printers/<id>/drawer-check` | Active cash drawer test |
| POST | `/api/printers/<id>/startup-report` | Print the status slip again |
| GET | `/api/network` | State of the network connection |
| POST | `/api/network/check` | Check the network right now |
| POST | `/api/printers/<id>/network-test` | Print the notice slip as a test |
| GET | `/api/update` | Update state (installed/available/backups) |
| POST | `/api/update/check` | Ask GitHub |
| POST | `/api/update/install` | `{"source": "online"}` or `{"source": "file", "file": "..."}` |
| POST | `/api/update/upload` | Upload an archive (raw file body, `?name=`) |
| GET | `/api/update/log` | Console output of the running update |
| GET | `/api/image/support` | Is image printing available? |
| POST | `/api/printers/<id>/image` | Upload an image, returns preview + token |
| POST | `/api/printers/<id>/image/print` | `{"token": "..."}` prints it |
| GET | `/docs`, `/docs/en/<file>.md` | Documentation as HTML |

Example:

```bash
curl -s http://192.168.1.50:8080/api/overview | python3 -m json.tool
curl -s -X POST http://192.168.1.50:8080/api/printers/printer1/test \
     -H 'Content-Type: application/json' -d '{"kind":"standard"}'
```
