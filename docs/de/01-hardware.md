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
| Raspberry Pi 1 B / B+ / Zero / Zero W | **funktioniert**, aber langsam | ARMv6, ein Kern mit 700 MHz, 256–512 MB RAM. Siehe [Raspberry Pi 1 und andere alte Boards](#raspberry-pi-1-und-andere-alte-boards). |
| Raspberry Pi 2 | funktioniert | ARMv7, vier Kerne. Deutlich flotter als ein Pi 1, sonst wie Pi 3. |
| Orange Pi Zero 3 / Radxa Zero u. ä. | funktioniert vermutlich | Nicht getestet. Voraussetzung: aktuelles Debian-basiertes Image mit systemd. |
| Luckfox Pico u. ä. (Buildroot) | nicht unterstützt | Kein `apt`, kein systemd im gewohnten Umfang. |
| OpenWrt-Router mit USB | nicht unterstützt | Technisch möglich (`p910nd`), aber Web-UI und Diagnose wären dort ein eigenes Projekt. |

## Raspberry Pi 1 und andere alte Boards

Kurz: **Ja, BonBridge läuft auf einem Raspberry Pi 1** (Model B, B+, A+) und
ebenso auf dem alten Pi Zero / Zero W. Es gibt nichts zu kompilieren und keine
Abhängigkeit, die einen modernen Prozessor braucht – das Programm ist reines
Python, alle Bibliotheken kommen als fertige `apt`-Pakete. Der Installer
akzeptiert die Architektur `armv6l` ausdrücklich.

**Passendes Betriebssystem.** Auf ARMv6 läuft **nur die 32-Bit-Ausgabe** von
Raspberry Pi OS. Das 64-Bit-Image startet auf einem Pi 1 gar nicht. Nimm im
Raspberry Pi Imager unter *Raspberry Pi OS (other)* den Eintrag
**Raspberry Pi OS Lite (32-bit)**. Die Lite-Variante ist bei 256–512 MB RAM
nicht optional, sondern nötig.

* Bookworm (32-Bit) bringt Python 3.11 mit – passt.
* Trixie (32-Bit) bringt Python 3.13 mit – passt ebenfalls, seit BonBridge
  1.1.1 (davor wäre die automatische Druckersuche dort still ausgefallen).
* Debian 13 „Trixie" ist die letzte Debian-Generation, die diese alten Boards
  trägt. Sicherheitsupdates laufen damit noch bis etwa 2030.

**Netzwerk per LAN-Kabel.** Beim Pi 1 **Model B / B+** ist die Ethernet-Buchse
kein eigener Netzwerkchip, sondern ein SMSC LAN9512/9514, der intern am selben
USB-Controller hängt wie die USB-Buchsen. Drucker und Netzwerk teilen sich also
eine USB-2.0-Leitung. Für Bondruck ist das völlig unkritisch: ein Bon sind
wenige Kilobyte, der Drucker selbst nimmt sie mit rund 9,6–115 kBit/s über die
Schnittstelle entgegen. Einfach Kabel einstecken, DHCP erledigt den Rest –
BonBridge bindet standardmäßig auf allen Adressen.

> **Feste IP vergeben.** Das gilt auf jedem Gerät, hier aber besonders: Das
> Kassensystem spricht den Drucker über die IP-Adresse an. Trage im Router eine
> DHCP-Reservierung auf die MAC-Adresse des Pi ein.

Der **Pi Zero / Zero W hat keine Ethernet-Buchse**. Wer dort Kabel will,
braucht einen USB-OTG-Hub mit LAN-Adapter – dann hängen Drucker und
Netzwerkadapter am selben Hub. Das funktioniert, ist aber teurer und fummeliger
als der Zero 2 W mit WLAN.

**Strom.** Der Drucker versorgt sich über sein eigenes 24-V-Netzteil, er zieht
also keinen Strom aus dem Pi – die schwachen Polyfuses des Pi 1 sind hier kein
Problem. Trotzdem ein ordentliches 5-V-Netzteil verwenden: Unterspannung ist
die häufigste Ursache für sporadische Aussetzer und wird auf der Seite
*Diagnose → Gerätestatus* ausdrücklich gemeldet.

**Was du an Tempo erwarten musst.** Der Pi 1 hat einen Kern mit 700 MHz. Der
Druckweg selbst ist davon praktisch nicht betroffen – ein Auftrag ist ein paar
Kilobyte, die Wartezeit bestimmt der Drucker. Spürbar langsamer sind:

* das Hochfahren nach dem Einschalten (gut eine Minute),
* der erste Aufruf der Weboberfläche,
* die Diagnoseseite, weil sie mehrere Systembefehle aufruft.

Damit die Weboberfläche nicht dauerhaft Last erzeugt, werden Werte wie
IP-Adressen und der Drosselungsstatus seit Version 1.1.2 zwischengespeichert
(15 bzw. 30 Sekunden), statt bei jeder Aktualisierung neu abgefragt zu werden.

**Nicht empfehlenswert auf einem Pi 1:** das optionale CUPS. Es wird für
BonBridge nicht gebraucht und kostet auf 256 MB RAM spürbar Speicher. Mehrere
Drucker gleichzeitig sind möglich, aber ein Pi 1 mit drei Druckern und offener
Weboberfläche ist nichts, was ich für den Dauerbetrieb empfehlen würde.

**Fazit:** Wenn ein Pi 1 herumliegt – aufsetzen und benutzen, für einen Drucker
reicht er. Für einen Neukauf ist der Pi Zero 2 W (ca. 23 €) die bessere Wahl:
vier Kerne, 512 MB, WLAN eingebaut und noch viele Jahre Betriebssystem-Updates.

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
* **Raspberry Pi OS Lite (32-Bit)** für Pi 1, Pi Zero / Zero W (ARMv6) – dort
  läuft die 64-Bit-Ausgabe nicht.
* Debian 11/12/13 oder Ubuntu 22.04+ auf x86.

Benötigt wird Python 3.9 oder neuer; das erfüllt jedes Raspberry Pi OS ab
Bullseye. Getestet wird gegen Python 3.9, 3.11, 3.12 und 3.13.

Beim Flashen mit dem Raspberry Pi Imager gleich WLAN, Hostname und SSH
konfigurieren – dann braucht das Gerät nie Bildschirm oder Tastatur.

Danach genügt:

```bash
curl -fsSL https://raw.githubusercontent.com/loe17/Bonbridge/main/install.sh | sudo bash
```
