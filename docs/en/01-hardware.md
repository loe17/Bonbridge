# Hardware: options, recommendation, bill of materials

BonBridge runs on any Debian based Linux with systemd. This page explains what
hardware makes sense - and what was evaluated and rejected.

## Recommendation in one sentence

**Raspberry Pi Zero 2 W** for a single printer, **Raspberry Pi 4** or a
second-hand x86 thin client when several printers or a wired LAN port are
needed.

## Supported platforms

| Platform | Status | Notes |
|---|---|---|
| Raspberry Pi Zero 2 W | **recommended** | Built-in Wi-Fi, tiny. Needs a USB-OTG adapter because it only has Micro-USB sockets. |
| Raspberry Pi 3 / 4 / 5 | **recommended** | Regular USB-A sockets, built-in Ethernet. On the Pi 4, prefer the black USB 2.0 ports if the printer is not detected. |
| x86-64 mini PC / thin client | **recommended** | Debian 11-13, Ubuntu 22.04+. Ideal if you already own one. |
| Raspberry Pi 1 B / B+ / Zero / Zero W | **works**, but slow | ARMv6, single core at 700 MHz, 256-512 MB RAM. See [Raspberry Pi 1 and other old boards](#raspberry-pi-1-and-other-old-boards). |
| Raspberry Pi 2 | works | ARMv7, four cores. Noticeably quicker than a Pi 1, otherwise like a Pi 3. |
| Orange Pi Zero 3, Radxa Zero, … | likely works | Untested. Needs a current Debian based image with systemd. |
| Luckfox Pico and similar (Buildroot) | not supported | No `apt`, no full systemd. |
| OpenWrt router with USB | not supported | Technically possible (`p910nd`), but the web interface and diagnostics would be a project of their own there. |

## Raspberry Pi 1 and other old boards

Short answer: **yes, BonBridge runs on a Raspberry Pi 1** (Model B, B+, A+) and
on the original Pi Zero / Zero W as well. There is nothing to compile and no
dependency that needs a modern CPU - the program is pure Python and every
library comes as a ready-made `apt` package. The installer explicitly accepts
the `armv6l` architecture.

**The right operating system.** ARMv6 only runs the **32-bit** build of
Raspberry Pi OS; the 64-bit image will not even boot on a Pi 1. In the
Raspberry Pi Imager pick **Raspberry Pi OS Lite (32-bit)** under *Raspberry Pi
OS (other)*. With 256-512 MB of RAM the Lite variant is not a preference, it is
a requirement.

* Bookworm (32-bit) ships Python 3.11 - fine.
* Trixie (32-bit) ships Python 3.13 - also fine as of BonBridge 1.1.1 (before
  that, printer auto-discovery would have failed silently there).
* Debian 13 "Trixie" is the last Debian generation to carry these old boards,
  which means security updates until roughly 2030.

**Networking over a LAN cable.** On the Pi 1 **Model B / B+** the Ethernet
socket is not a separate network chip but an SMSC LAN9512/9514 sitting on the
very same USB controller as the USB sockets. Printer and network therefore
share one USB 2.0 link. For receipt printing that is irrelevant: a receipt is a
few kilobytes and the printer itself accepts them at roughly 9.6-115 kbit/s
over its interface. Plug the cable in, DHCP does the rest - BonBridge binds to
all addresses by default.

> **Assign a fixed IP.** True on any device, but especially here: the POS
> system addresses the printer by IP address. Add a DHCP reservation for the
> Pi's MAC address in your router.

The **Pi Zero / Zero W has no Ethernet socket** at all. Cabled networking there
needs a USB-OTG hub with a LAN adapter, so printer and network adapter share
that hub. It works, but it is more expensive and more fiddly than a Zero 2 W
over Wi-Fi.

**Power.** The printer runs from its own 24 V supply and draws nothing from the
Pi, so the Pi 1's weak polyfuses are not a concern. Still use a decent 5 V
supply: under-voltage is the most common cause of sporadic dropouts, and
*Diagnostics -> Device status* reports it explicitly.

**What to expect in terms of speed.** The Pi 1 has a single 700 MHz core. The
print path itself is barely affected - a job is a few kilobytes and the printer
sets the pace. Noticeably slower are:

* booting after power-on (a good minute),
* the first load of the web interface,
* the diagnostics page, because it runs several system commands.

So that the web interface does not create constant load, values such as IP
addresses and the throttling status have been cached since version 1.1.2 (15
and 30 seconds respectively) instead of being re-read on every refresh.

**Not recommended on a Pi 1:** the optional CUPS installation. BonBridge does
not need it and it costs real memory on a 256 MB board. Several printers on one
device are possible, but a Pi 1 driving three printers with the web interface
open is not something I would recommend for continuous operation.

**Bottom line:** if a Pi 1 is lying around, set it up and use it - it is enough
for one printer. For a new purchase the Pi Zero 2 W (about 23 EUR) is the
better choice: four cores, 512 MB, built-in Wi-Fi and many more years of OS
updates.

## Why not an ESP32?

A fair question - an ESP32 costs a tenth of a Raspberry Pi. Two routes were
evaluated:

**ESP32-S3 as a USB host.** The classic ESP32 has no USB host at all; only the
S2/S3 have USB-OTG. A USB **printer class** host driver is not part of ESP-IDF.
Community demos exist
([`touchgadget/esp32-usb-host-demos`](https://github.com/touchgadget/esp32-usb-host-demos)),
whose author states they only show that it is possible in principle. On top of
that, the usual dev kits provide no 5 V on VBUS, so an external feed and a
custom cable are required. Printers that present a vendor specific interface
(Epson TM-M244A, TM-m30 family) would additionally need their own class driver.

**ESP32 + RS-232.** This is the only ESP32 route that is genuinely stable
(UART + MAX3232 into an Epson UB-S01 board). But it needs an extra interface
board costing roughly 30-60 EUR, which makes the solution **more expensive
than a Pi Zero 2 W** while doing considerably less.

**Conclusion:** the ESP32 is not a product target. The wiring diagram for the
serial route is still in [02-wiring.md](02-wiring.md) if you want to
experiment.

## The honest alternative: no bridge at all

If the printer gets a network interface, the POS application talks to it
directly and BonBridge is not needed:

* **Epson UB-E04** (Ethernet) or **UB-R04** (Wi-Fi) - the TM-T88V's interface
  boards are exchangeable. Roughly 50-80 EUR depending on the source.
* A new printer with built-in networking (for example the Epson TM-m30 III),
  which OrderAssist explicitly lists as tested.

Do the maths: a Pi Zero 2 W plus accessories is about 45 EUR, a UB-E04 about
60 EUR. The bridge pays off mainly when you also want diagnostics, spooling
and a web interface - or when you want to serve several print groups from one
device.

## Bill of materials "BonBridge Zero"

| Part | approx. |
|---|---|
| Raspberry Pi Zero 2 W | 23 EUR |
| 5 V / 2.5 A Micro-USB power supply | 9 EUR |
| microSD 16 GB (class A1) | 7 EUR |
| USB-OTG adapter Micro-USB → USB-A | 4 EUR |
| USB cable A → B (printer cable) | 5 EUR |
| Case / 3D printed mount | 0-8 EUR |
| **Total** | **~48-56 EUR** |

Prices are indicative (August 2026, Germany) and change.

**Additionally mandatory:** the printer's **own 24 V power supply** (Epson
PS-180). The Pi does not power the printer - without 24 V the printer does not
even enumerate over USB.

## Operating system

* **Raspberry Pi OS Lite (64-bit)** - recommended, no desktop needed.
* **Raspberry Pi OS Lite (32-bit)** for the Pi 1 and Pi Zero / Zero W (ARMv6) -
  the 64-bit build does not run there.
* Debian 11/12/13 or Ubuntu 22.04+ on x86.

Python 3.9 or newer is required, which every Raspberry Pi OS from Bullseye
onwards satisfies. Testing runs against Python 3.9, 3.11, 3.12 and 3.13.

When flashing with the Raspberry Pi Imager, configure Wi-Fi, hostname and SSH
right away - then the device never needs a screen or keyboard.

After that:

```bash
curl -fsSL https://raw.githubusercontent.com/loe17/Bonbridge/main/install.sh | sudo bash
```
