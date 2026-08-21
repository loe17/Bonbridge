# BonBridge

**Turn a Raspberry Pi or any small Linux box into a network receipt printer.**

Many POS applications - OrderAssist among them - can only address a receipt
printer by **IP address on port 9100**. USB and serial printers are simply not
supported. BonBridge closes that gap: it attaches to a USB or serial ESC/POS
printer and presents it on the network exactly like a printer with a built-in
Ethernet interface, plus a web interface for status, diagnostics and setup.

> 🇩🇪 **[Deutsche Fassung dieser Seite → README.de.md](README.de.md)** ·
> Full documentation: [`docs/en/`](docs/en/) · [`docs/de/`](docs/de/)

---

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/loe17/Bonbridge/main/install.sh | sudo bash
```

That is the whole installation. It works on

| Platform | Notes |
|---|---|
| Raspberry Pi Zero 2 W | recommended, needs a USB-OTG adapter |
| Raspberry Pi 3 / 4 / 5 | plug the printer into a USB-A port (Pi 4: prefer the black USB 2.0 ports) |
| x86-64 mini PC / thin client | Debian 11-13, Ubuntu 22.04+ |
| Raspberry Pi 1 / 2 / Zero (ARMv6, ARMv7) | works - use the **32-bit** Lite image, see [hardware](docs/en/01-hardware.md#raspberry-pi-1-and-other-old-boards) |

No compiler, no `pip`, no third-party git clone at install time - everything
BonBridge needs is either a Debian package or bundled in `vendor/`.

Afterwards:

```
Web interface :  http://<ip>:8080/
Documentation :  http://<ip>:8080/docs
POS printing  :  <ip>  port 9100  (RAW / ESC-POS)
```

You do not have to hunt for the IP address: **BonBridge prints a slip with its
own address, the port and the POS settings every time it starts.**

### Update and uninstall

```bash
sudo bonbridge update              # check for a new version and install it
sudo bonbridge update --check      # only look, change nothing
sudo bonbridge update --rollback   # undo the last update

sudo bash /opt/bonbridge/uninstall.sh           # remove, keep the configuration
sudo bash /opt/bonbridge/uninstall.sh --purge   # remove everything, including
                                                # /etc/bonbridge and /var/lib/bonbridge
```

Uninstalling stops and removes the service, the unit files and the program
directory. CUPS, avahi and the Python packages are left installed, because
other software may be using them.

## What it does

* **RAW/JetDirect listener on port 9100** - what POS applications expect.
* **Bidirectional** communication with the printer, so paper end, open cover
  and cutter errors are actually visible instead of jobs disappearing silently.
* **One owner per printer.** A single worker thread writes to the device, so
  jobs can never interleave. Failed jobs are spooled and retried instead of
  being lost.
* **Automatic printer identification** from USB descriptors, the IEEE-1284
  device ID and the ESC/POS `GS I` printer ID, matched against a bundled
  capability database of ~50 printer models.
* **It tells you what to type into your POS app.** Font, character set and
  line width are read out of the printer profile instead of being found by
  trial and error.
* **Several print groups from one device.** POS apps address printers by IP
  only, so BonBridge can bind each printer to its own IP alias, all on 9100.
* **Feature switches.** Cutter, cash drawer, buzzer, barcode, QR, graphics -
  each detected automatically and each overridable in the web interface.
* **Works with several transports:** libusb (also for printers that never
  create `/dev/usb/lp0`, such as the Epson TM-m30 family), kernel `usblp`,
  serial/RS-232 and network.
* **CUPS is optional**, not required. When enabled, its queue prints *through*
  BonBridge rather than fighting it for the device.
* **Prints its own address on start-up**, so a device without a screen still
  tells you where to point the app.
* **Explains every warning.** Each traffic light expands into the individual
  checks - under-voltage, temperature, disk, listener, paper - with what to do.
* **Print receipts from the browser** with a live preview in the real paper
  width.
* **Documentation on the device**, rendered as HTML at `/docs`, no internet
  needed.

## Quick check

```bash
bonbridge scan                 # which printers can be used?
bonbridge report > report.txt  # full support report
systemctl status bonbridge
journalctl -u bonbridge -f
```

## Connecting OrderAssist

1. `Drucker` → `+ Hinzufügen` → enter the **IP address** shown in the
   BonBridge web interface. The port is fixed at 9100 in the app.
2. Open **Integration** in the BonBridge web interface and copy the font,
   character set and line width values into the app.
3. Print a test page and assign the printer to a print group.

Details: [`docs/en/04-pos-integration.md`](docs/en/04-pos-integration.md)

## Documentation

| | English | Deutsch |
|---|---|---|
| Hardware & options | [01-hardware.md](docs/en/01-hardware.md) | [01-hardware.md](docs/de/01-hardware.md) |
| Wiring diagrams | [02-wiring.md](docs/en/02-wiring.md) | [02-anschlussplan.md](docs/de/02-anschlussplan.md) |
| Printer configuration | [03-printer-setup.md](docs/en/03-printer-setup.md) | [03-drucker-konfiguration.md](docs/de/03-drucker-konfiguration.md) |
| POS integration | [04-pos-integration.md](docs/en/04-pos-integration.md) | [04-orderassist.md](docs/de/04-orderassist.md) |
| Web interface | [05-web-interface.md](docs/en/05-web-interface.md) | [05-weboberflaeche.md](docs/de/05-weboberflaeche.md) |
| Diagnostics & FAQ | [06-diagnostics.md](docs/en/06-diagnostics.md) | [06-diagnose.md](docs/de/06-diagnose.md) |
| Several print groups | [07-print-groups.md](docs/en/07-print-groups.md) | [07-ausdruckgruppen.md](docs/de/07-ausdruckgruppen.md) |
| Architecture | [08-architecture.md](docs/en/08-architecture.md) | [08-architektur.md](docs/de/08-architektur.md) |
| **Third-party code & sources** | [09-references.md](docs/en/09-references.md) | [09-referenzen.md](docs/de/09-referenzen.md) |
| **Updates, network watchdog, maintenance** | [10-updates.md](docs/en/10-updates.md) | [10-updates.md](docs/de/10-updates.md) |

## Licence

MIT for BonBridge itself. Bundled components keep their own licences - see
[`NOTICE`](NOTICE) and the annotated list in
[`docs/en/09-references.md`](docs/en/09-references.md), which names every piece
of third-party code, its licence and where it is used:
[zj-58](https://github.com/klirichek/zj-58) (BSD-2-Clause, CUPS filter) and
[escpos-printer-db](https://github.com/receipt-print-hq/escpos-printer-db)
(CC BY 4.0, printer capability database). BonBridge is not affiliated with Seiko Epson or with
OrderAssist.
