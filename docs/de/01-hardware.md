# Hardware: Optionen, Empfehlung, Stückliste

BonBridge läuft auf jedem Debian-basierten Linux mit systemd. Diese Seite
erklärt, welche Hardware sinnvoll ist – und welche geprüft und verworfen wurde.

## Empfehlung in einem Satz

**Raspberry Pi Zero 2 W** für einen Drucker, **Raspberry Pi 4** oder ein
gebrauchter x86-Thin-Client, wenn mehrere Drucker oder eine LAN-Buchse
gebraucht werden.

## Unterstützte Plattformen

| Plattform | Status | Hinweise |
|---|---|---|
| Raspberry Pi Zero 2 W | **empfohlen** | WLAN eingebaut, sehr klein. Braucht einen USB-OTG-Adapter, weil nur Micro-USB-Buchsen vorhanden sind. |
| Raspberry Pi 3 / 4 / 5 | **empfohlen** | Normale USB-A-Buchsen, LAN eingebaut. Beim Pi 4 bei Problemen die schwarzen USB-2.0-Ports statt der blauen 3.0-Ports nutzen. |
| x86-64 Mini-PC / Thin Client | **empfohlen** | Debian 11–13, Ubuntu 22.04+. Ideal, wenn ohnehin ein Gerät vorhanden ist. |
| Orange Pi Zero 3 / Radxa Zero u. ä. | funktioniert vermutlich | Nicht getestet. Voraussetzung: aktuelles Debian-basiertes Image mit systemd. |
| Luckfox Pico u. ä. (Buildroot) | nicht unterstützt | Kein `apt`, kein systemd im gewohnten Umfang. |
| OpenWrt-Router mit USB | nicht unterstützt | Technisch möglich (`p910nd`), aber Web-UI und Diagnose wären dort ein eigenes Projekt. |

## Warum kein ESP32?

Die Frage ist berechtigt – ein ESP32 kostet ein Zehntel eines Raspberry Pi.
Geprüft wurden zwei Wege:

**ESP32-S3 als USB-Host.** Der klassische ESP32 hat gar keinen USB-Host; nur
S2/S3 haben USB-OTG. Ein USB-**Printer-Class**-Host-Treiber ist in ESP-IDF
nicht enthalten. Es existieren Community-Demos
([`touchgadget/esp32-usb-host-demos`](https://github.com/touchgadget/esp32-usb-host-demos)),
deren Autor selbst schreibt, sie zeigten nur, dass es prinzipiell geht.
Dazu kommt: Die üblichen DevKits liefern keine 5 V auf VBUS, es braucht also
eine externe Einspeisung und ein Custom-Kabel. Drucker, die sich
vendor-spezifisch melden (Epson TM-M244A, TM-m30-Familie), bräuchten zusätzlich
einen eigenen Klassentreiber.

**ESP32 + RS-232.** Das ist der einzige ESP32-Weg, der wirklich stabil
funktioniert (UART + MAX3232 an ein Epson UB-S01-Board). Er kostet aber ein
zusätzliches Interface-Board von rund 30–60 €. Damit ist die Lösung **teurer
als ein Pi Zero 2 W** und kann deutlich weniger.

**Ergebnis:** ESP32 ist kein Produktziel. Der Anschlussplan für den seriellen
Weg steht trotzdem in [02-anschlussplan.md](02-anschlussplan.md), falls du
damit experimentieren willst.

## Die ehrliche Alternative: gar keine Bridge

Wenn der Drucker eine Netzwerkschnittstelle bekommt, spricht das Kassensystem
direkt mit ihm und BonBridge wird nicht gebraucht:

* **Epson UB-E04** (Ethernet) oder **UB-R04** (WLAN) – die Interface-Boards des
  TM-T88V sind austauschbar. Kosten je nach Quelle ca. 50–80 €.
* Ein neuer Drucker mit eingebautem Netzwerk (z. B. Epson TM-m30 III), den
  OrderAssist ausdrücklich als getestet führt.

Rechnung: Ein Pi Zero 2 W samt Zubehör kostet ~45 €, ein UB-E04 ~60 €. Die
Bridge lohnt sich also vor allem dann, wenn du zusätzlich Diagnose,
Zwischenspeicherung und eine Weboberfläche willst – oder mehrere
Ausdruckgruppen aus einem Gerät bedienen möchtest.

## Stückliste „BonBridge Zero"

| Teil | ca. |
|---|---|
| Raspberry Pi Zero 2 W | 23 € |
| Netzteil 5 V / 2,5 A Micro-USB | 9 € |
| microSD 16 GB (Class A1) | 7 € |
| USB-OTG-Adapter Micro-USB → USB-A | 4 € |
| USB-Kabel A → B (Druckerkabel) | 5 € |
| Gehäuse / 3D-Druck-Halterung | 0–8 € |
| **Summe** | **~48–56 €** |

Preise sind Anhaltswerte (Stand August 2026, DE) und ändern sich.

**Zusätzlich zwingend:** das **eigene 24-V-Netzteil des Druckers**
(Epson PS-180). Der Pi versorgt den Drucker nicht – ohne 24 V meldet sich der
Drucker nicht einmal am USB an.

## Betriebssystem

* **Raspberry Pi OS Lite (64-Bit)** – empfohlen, kein Desktop nötig.
* Debian 11/12/13 oder Ubuntu 22.04+ auf x86.

Beim Flashen mit dem Raspberry Pi Imager gleich WLAN, Hostname und SSH
konfigurieren – dann braucht das Gerät nie Bildschirm oder Tastatur.

Danach genügt:

```bash
curl -fsSL https://raw.githubusercontent.com/loe17/Bonbridge/main/install.sh | sudo bash
```
