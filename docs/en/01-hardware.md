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
| Orange Pi Zero 3, Radxa Zero, … | likely works | Untested. Needs a current Debian based image with systemd. |
| Luckfox Pico and similar (Buildroot) | not supported | No `apt`, no full systemd. |
| OpenWrt router with USB | not supported | Technically possible (`p910nd`), but the web interface and diagnostics would be a project of their own there. |

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
* Debian 11/12/13 or Ubuntu 22.04+ on x86.

When flashing with the Raspberry Pi Imager, configure Wi-Fi, hostname and SSH
right away - then the device never needs a screen or keyboard.

After that:

```bash
curl -fsSL https://raw.githubusercontent.com/loe17/bonbridge/main/install.sh | sudo bash
```
