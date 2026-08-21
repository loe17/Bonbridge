# Referenzen: verwendeter Fremdcode und Quellen

Diese Seite listet **jeden fremden Code, jede Datenquelle und jede
Spezifikation**, auf der BonBridge aufbaut – mit Link, Lizenz und der Stelle im
Projekt, an der sie benutzt wird.

Die maschinenlesbare Kurzfassung steht in [`NOTICE`](../../NOTICE).

---

## 1. Mitgelieferter Fremdcode (`vendor/`)

Beide Komponenten liegen **als Kopie im Repository**. Das ist Absicht: Die
Installation soll auch dann noch funktionieren, wenn eines dieser Projekte von
GitHub verschwindet. In jedem Verzeichnis steht in `VENDORED_COMMIT`, aus
welchem Upstream-Stand die Kopie stammt.

### 1.1 zj-58 — CUPS-Filter für ESC/POS-Drucker

| | |
|---|---|
| **Projekt** | [klirichek/zj-58](https://github.com/klirichek/zj-58) |
| **Autor** | Aleksey N. Vinogradov |
| **Lizenz** | [BSD 2-Clause](https://github.com/klirichek/zj-58/blob/master/LICENSE) — erlaubt das Mitliefern |
| **Liegt bei uns unter** | [`vendor/zj-58/`](../../vendor/zj-58/) |
| **Wird benutzt von** | dem **optionalen** CUPS-Modul: [`install.sh`](../../install.sh) (`--with-cups`) und [`packaging/cups/setup-cups.sh`](../../packaging/cups/setup-cups.sh) |
| **Wofür genau** | Rastert CUPS-Druckdaten (also normale Dokumente, Testseiten aus dem Betriebssystem) in ESC/POS-Bitmaps um. Enthält die PPD-Dateien `zj58.ppd` (58 mm) und `zj80.ppd` (80 mm). |
| **Nicht nötig für** | OrderAssist. Der Kassendruck läuft über RAW/9100 komplett ohne CUPS und ohne zj-58. |

Übernommene Dateien:

| Datei | Zweck |
|---|---|
| [`vendor/zj-58/rastertozj.c`](../../vendor/zj-58/rastertozj.c) | der eigentliche CUPS-Filter |
| [`vendor/zj-58/zj58.ppd`](../../vendor/zj-58/zj58.ppd), [`zj80.ppd`](../../vendor/zj-58/zj80.ppd) | Druckerbeschreibungen 58 / 80 mm |
| [`vendor/zj-58/zjdrv.drv`](../../vendor/zj-58/zjdrv.drv) | Quelle, aus der die PPDs erzeugt werden |
| [`vendor/zj-58/CMakeLists.txt`](../../vendor/zj-58/CMakeLists.txt) | Build |
| [`vendor/zj-58/LICENSE`](../../vendor/zj-58/LICENSE) | unveränderte Lizenz des Originals |

> Das alte Projekt hat zj-58 **zur Installationszeit von GitHub geklont und
> kompiliert**. Genau das ist jetzt weg: Der Code liegt im Repo, und er wird
> nur noch gebaut, wenn du CUPS überhaupt willst.

### 1.2 escpos-printer-db — Druckermodell-Datenbank

| | |
|---|---|
| **Projekt** | [receipt-print-hq/escpos-printer-db](https://github.com/receipt-print-hq/escpos-printer-db) |
| **Durchsuchbare Fassung** | <https://mike42.me/escpos-printer-db/> |
| **Lizenz** | [Creative Commons Attribution 4.0](https://github.com/receipt-print-hq/escpos-printer-db/blob/master/LICENSE.md) — Namensnennung erfolgt hier und in [`NOTICE`](../../NOTICE) |
| **Liegt bei uns unter** | [`vendor/escpos-printer-db/capabilities.json`](../../vendor/escpos-printer-db/capabilities.json) |
| **Wird benutzt von** | [`src/bonbridge/caps.py`](../../src/bonbridge/caps.py) → `load_capability_db()`, `get_profile()`, `profile_features()`, `recommend_pos_settings()` |
| **Wofür genau** | Liefert je Modell: Fonts und Zeichen pro Zeile, Papierbreite und Auflösung, unterstützte Codepages sowie die Funktionsflags (Cutter, Kassenlade, Barcode, QR, PDF417, Grafik). Daraus entstehen die Statusampel-Funktionsmatrix und die **empfohlenen Werte für das Kassensystem**. |
| **Umfang** | rund 50 Modelle, darunter `TM-T88V`, `TM-m30III`, `TM-T20III`, `ITPP047` (Munbyn), `ZJ-5870` |

Konkretes Beispiel: Dass BonBridge für deinen TM-T88V `font2` / `cp1252` /
`56 Zeichen` vorschlägt, stammt direkt aus dem Eintrag `TM-T88V` dieser
Datenbank (`fonts."1".columns = 56`, `codePages."16" = CP1252`).

Eigene Ergänzungen zu dieser Datenbank liegen als YAML unter
[`src/bonbridge/profiles/`](../../src/bonbridge/profiles/) – sie fügen
Erkennungshinweise (USB-Produktstrings) und Einrichtungstexte hinzu, ohne die
Originaldaten zu verändern.

---

## 2. Laufzeit-Abhängigkeiten (nicht mitgeliefert, aus der Distribution)

| Paket | Projekt | Lizenz | Benutzt in |
|---|---|---|---|
| `python3` | [python.org](https://www.python.org/) | PSF | überall |
| `python3-usb` (PyUSB) | [pyusb/pyusb](https://github.com/pyusb/pyusb) | BSD-3-Clause | [`transports/usb_libusb.py`](../../src/bonbridge/transports/usb_libusb.py) |
| `python3-serial` (pySerial) | [pyserial/pyserial](https://github.com/pyserial/pyserial) | BSD-3-Clause | [`transports/serial_port.py`](../../src/bonbridge/transports/serial_port.py) |
| `python3-yaml` (PyYAML) | [yaml/pyyaml](https://github.com/yaml/pyyaml) | MIT | [`config.py`](../../src/bonbridge/config.py), [`caps.py`](../../src/bonbridge/caps.py) |
| `libusb-1.0` | [libusb/libusb](https://github.com/libusb/libusb) | LGPL-2.1-or-later | unter PyUSB |
| `avahi-daemon` | [avahi.org](https://www.avahi.org/) | LGPL-2.1-or-later | [`mdns.py`](../../src/bonbridge/mdns.py) (optional) |
| `python3-zeroconf` | [python-zeroconf/python-zeroconf](https://github.com/python-zeroconf/python-zeroconf) | LGPL-2.1 | [`mdns.py`](../../src/bonbridge/mdns.py) (optional, nur wenn installiert) |
| `cups` | [OpenPrinting CUPS](https://github.com/OpenPrinting/cups) | Apache-2.0 | optionales CUPS-Modul |
| `iproute2` | [iproute2](https://git.kernel.org/pub/scm/network/iproute2/iproute2.git) | GPL-2.0 | [`sysinfo.py`](../../src/bonbridge/sysinfo.py), [`packaging/bin/bonbridge-ip`](../../packaging/bin/bonbridge-ip) |

Bewusst **nicht** verwendet: Web-Framework, ORM, Build-Toolchain, npm. Der
Webserver ist die Standardbibliothek
([`http.server`](https://docs.python.org/3/library/http.server.html)), die
Oberfläche eine einzelne HTML-Datei mit reinem JavaScript.

---

## 3. Protokolle und Spezifikationen

### ESC/POS (Seiko Epson)

| Quelle | Wofür im Code |
|---|---|
| [ESC/POS Command Reference (Epson)](https://download4.epson.biz/sec_pubs/pos/reference_en/escpos/index.html) | Grundlage von [`escpos.py`](../../src/bonbridge/escpos.py) |
| [TM-T88V: unterstützte Befehle](https://download4.epson.biz/sec_pubs/pos/reference_en/escpos/tmt88v.html) | Abgleich, welche Befehle der TM-T88V wirklich kennt |
| [TM-T88V Technical Reference Guide (PDF)](https://files.support.epson.com/pdf/pos/bulk/tm-t88v_trg_en_revf.pdf) | DIP-Schalter, Memory-Switches, Interface-Boards → [03-drucker-konfiguration.md](03-drucker-konfiguration.md) |
| [TM-T88VI Technical Reference Guide (PDF)](https://files.support.epson.com/pdf/pos/bulk/tm-t88vi_trg_en_revg.pdf) | Gegenprüfung neuerer Modelle |

Konkret benutzte Befehle und wo sie im Code stehen
([`src/bonbridge/escpos.py`](../../src/bonbridge/escpos.py)):

| Befehl | Bytes | Funktion im Code | Wofür |
|---|---|---|---|
| `ESC @` | `1B 40` | `INIT` | Drucker zurücksetzen |
| `ESC t n` | `1B 74 n` | `select_codepage()` | Zeichensatz (cp1252 = 16) |
| `ESC M n` | `1B 4D n` | `select_font()` | Font A / Font B |
| `ESC a n` | `1B 61 n` | `align()` | Ausrichtung |
| `ESC d n` | `1B 64 n` | `feed()` | Papiervorschub |
| `ESC p m t1 t2` | `1B 70 …` | `drawer_pulse()` | Kassenlade |
| `ESC ( A` | `1B 28 41 …` | `buzzer()` | Signalton |
| `GS V m n` | `1D 56 …` | `cut()` | Papierschnitt |
| `GS ( k` | `1D 28 6B …` | `qrcode()` | QR-Code |
| `GS k 4` | `1D 6B 04 …` | `barcode_code39()` | CODE39-Barcode |
| `GS I n` | `1D 49 n` | `GS_I_MODEL/TYPE/ROM` | Drucker-Identifikation |
| `GS r n` | `1D 72 n` | `GS_R_PAPER/DRAWER` | Papier- und Ladenstatus |
| `GS a n` | `1D 61 n` | `enable_asb()` | Automatic Status Back |
| `DLE EOT n` | `10 04 n` | `STATUS_DECODERS` | Echtzeitstatus (Papier, Deckel, Fehler) |

Die Statusbits werden in `decode_printer_status()`, `decode_offline_status()`,
`decode_error_status()` und `decode_paper_status()` ausgewertet.

### RAW / JetDirect (Port 9100)

Kein formaler Standard, sondern die von HP eingeführte Praxis „TCP-Verbindung
auf 9100, Bytes rein, Drucker druckt". Umgesetzt in
[`raw_server.py`](../../src/bonbridge/raw_server.py). Verwandte Referenzen:

* [RFC 1179 – Line Printer Daemon Protocol](https://datatracker.ietf.org/doc/html/rfc1179) (LPD, die ältere Alternative)
* [CUPS `socket`-Backend](https://www.cups.org/doc/network.html) – die Gegenstelle, wenn ein Linux-Rechner auf BonBridge druckt

### mDNS / DNS-SD

* [RFC 6762 – Multicast DNS](https://datatracker.ietf.org/doc/html/rfc6762)
* [RFC 6763 – DNS-Based Service Discovery](https://datatracker.ietf.org/doc/html/rfc6763)
* Service-Typen: `_pdl-datastream._tcp` (RAW-Druck) und `_http._tcp`
  ([IANA-Registry](https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml))

Umgesetzt in [`mdns.py`](../../src/bonbridge/mdns.py).

### Auffindbarkeit: welche Protokolle ein Epson-Netzwerkboard spricht

Die maßgebliche Primärquelle ist die technische Referenz des Interface-Boards
des TM-T88V. Dort stehen alle Protokolle, die ein echtes Gerät beantwortet —
und damit die Liste, die BonBridge nachbildet:

* [Epson UB-E04 Technical Reference Guide](https://files.support.epson.com/pdf/ube04_/ube04_trg.pdf) — LPR (515), RAW (9100), SNMP v1 (161, Community `public`), ENPC (3289, Pakettypen Probe/Initialize/Query/Setup/Notify), mDNS, HTTP

### ENPC (Epson-Netzwerksuche, UDP 3289) — teilweise rekonstruiert

Epson veröffentlicht das **Antwortformat nicht**. Der Rahmenaufbau in
[`discovery.py`](../../src/bonbridge/discovery.py) beruht auf öffentlichen
Analysen Dritter; deshalb sendet BonBridge wahlweise mehrere Antwortvarianten
und protokolliert jede Anfrage mit Hexdump, statt eine Formatvermutung als
Tatsache auszugeben:

* [BlackLotus/epson-stuff — `enpc.lua`](https://github.com/BlackLotus/epson-stuff/blob/master/enpc.lua) — **Wireshark-Dissektor mit dem vollstaendigen Headeraufbau**: Geraetetyp, Geraetenummer, Funktion (16 Bit), Ergebniscode, Nutzdatenlaenge (16 Bit). Die maßgebliche Quelle für `discovery.py`
* [wes4m: „Reverse Engineering Thermal Printers"](https://wes4m.io/posts/epson_rev/) — Mitschnitte eines echten TM-m30 und ein funktionierender Emulator mit allen fünf Antwortvorlagen
* [mike42/escpos-php Issue #923: „Need help with ENPC protocol 3289"](https://github.com/mike42/escpos-php/issues/923) — das beobachtete 16-Byte-Suchpaket des ePOS-SDK
* [Epson ePOS SDK: `Discovery.start`](https://download4.epson.biz/sec_pubs/pos/reference_en/epos_and/ref_epos_sdk_and_en_discoveryclass_start.html) — offizielle Client-Seite

### SNMP (UDP 161)

Vollständig öffentlich spezifiziert; die Umsetzung in
[`snmp.py`](../../src/bonbridge/snmp.py) kodiert BER von Hand, um ohne
`pysnmp` auszukommen:

* [RFC 1157 — Simple Network Management Protocol (v1)](https://datatracker.ietf.org/doc/html/rfc1157)
* [RFC 1213 — MIB-II](https://datatracker.ietf.org/doc/html/rfc1213) (`sysDescr`, `sysName`, `sysObjectID`)
* [RFC 2790 — Host Resources MIB](https://datatracker.ietf.org/doc/html/rfc2790) (`hrDeviceDescr`, `hrPrinterStatus`)
* [RFC 3805 — Printer MIB v2](https://datatracker.ietf.org/doc/html/rfc3805) (`prtGeneralPrinterName`)
* Epsons IANA-Enterprise-Nummer ist **1248** → `sysObjectID = 1.3.6.1.4.1.1248`

### IEEE 1284 Device ID

Wird aus `/sys/class/usbmisc/lp*/device/ieee1284_id` gelesen
([`transports/usblp.py`](../../src/bonbridge/transports/usblp.py)) und liefert
`MFG:`/`MDL:`/`SN:` für die Modellerkennung.
Referenz: [Linux `usblp`-Treiber](https://www.kernel.org/doc/html/latest/usb/index.html)

---

## 4. Kassensystem-Dokumentation

| Quelle | Was daraus stammt |
|---|---|
| [OrderAssist – Drucker](https://doku.order-assist.de/docs/handbuch/drucker/) | Drucker werden **nur über die IP** hinzugefügt, Port ist fest 9100; die automatische Suche findet nur EPSON-Geräte; Felder Schriftart / Zeichensatz / Zeilenbreite; Aufbau der Testseite |
| [OrderAssist – Empfohlene Hardware](https://doku.order-assist.de/docs/empfohlene-hardware) | **USB und seriell werden nicht unterstützt** – die Begründung für dieses Projekt |
| [OrderAssist – Ausdruckgruppen](https://doku.order-assist.de/docs/handbuch/ausdruckgruppen/) | Warum mehrere Drucker mehrere IP-Adressen brauchen → [07-ausdruckgruppen.md](07-ausdruckgruppen.md) |

Die BonBridge-Testseite in `escpos.test_page()` ist bewusst der
OrderAssist-Testseite nachgebaut (Zeichen-Lineal, Sonderzeichen, Ausrichtung,
Tabelle, Divider, QR), damit man beide direkt vergleichen kann.

---

## 5. Vorgänger und verwandte Projekte

Nicht als Code übernommen, aber als Vorlage, Gegenprobe oder Alternative
ausgewertet:

| Projekt | Was daraus einging |
|---|---|
| [loe17/OrderAssist-over-Raspberry-Pi-with-Epson-TM-T88V](https://github.com/loe17/OrderAssist-over-Raspberry-Pi-with-Epson-TM-T88V) | Der direkte Vorgänger dieses Repos (CUPS + zj-58 + socat). Die Erkenntnis „RAW auf 9100, kein IPP" stammt von dort. Umstieg: [`MIGRATION.md`](../../MIGRATION.md) |
| [plinth666/epsonsimplecups](https://github.com/plinth666/epsonsimplecups) | Alternativer, sehr schlanker CUPS-Treiber für Epson TM-T20 – als Gegenprobe zu zj-58 |
| [trandi/esp32-thermal_printer](https://github.com/trandi/esp32-thermal_printer) | ESP32 + serielle Ansteuerung eines TM-T88 – Grundlage der ESP32-Bewertung in [01-hardware.md](01-hardware.md) |
| [touchgadget/esp32-usb-host-demos](https://github.com/touchgadget/esp32-usb-host-demos) | Experimenteller USB-Host-Druckertreiber für ESP32-S2/S3 – zeigt, dass der Weg technisch möglich, aber nicht produktreif ist |
| [Aaron Chambers: T88V Raspberry-Pi-Halterung (Printables)](https://www.printables.com/model/1340272-t88v-raspberry-pi-full-size-mount) | 3D-Druck-Halterung für Pi + TM-T88V, erwähnt in der Stückliste |
| [Elektronik-Kompendium: Print-Server mit CUPS und AirPrint](https://www.elektronik-kompendium.de/sites/raspberry-pi/2007081.htm) | Referenz für die klassische CUPS-Variante |
| [Deutsches Raspberry-Pi-Forum: TM-T88VI über CUPS](https://forum-raspberrypi.de/forum/thread/60662-epson-tm-t-88vi-mit-cups-ueber-netzwerk-ansteuern/) | Praxisberichte zu Epson + CUPS |
| [python-escpos](https://github.com/python-escpos/python-escpos) | **Kein Code übernommen** – aber die gemeinsame Nutzung der escpos-printer-db und deren Profil-Semantik orientiert sich daran |
| [mike42/escpos-php](https://github.com/mike42/escpos-php) | dito, plus die ENPC-Recherche |

---

## 6. Lizenzlage in einem Satz

BonBridge selbst steht unter der [MIT-Lizenz](../../LICENSE). Der mitgelieferte
zj-58-Code bleibt BSD-2-Clause, die mitgelieferte Modelldatenbank bleibt
CC BY 4.0. Beide Lizenzen erlauben die Weitergabe im Repository, verlangen aber
die Nennung von Copyright bzw. Urheberschaft – die steht in
[`NOTICE`](../../NOTICE) und auf dieser Seite.

ESC/POS ist eine Marke der Seiko Epson Corporation. BonBridge implementiert nur
den öffentlich dokumentierten Befehlssatz und steht in keiner Verbindung zu
Seiko Epson oder zu OrderAssist.
