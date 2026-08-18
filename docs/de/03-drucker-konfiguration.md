# Drucker richtig konfigurieren

Ein Bondrucker kann elektrisch einwandfrei angeschlossen sein und trotzdem
nicht drucken, weil er im falschen Modus läuft. Diese Seite beschreibt, was am
Gerät selbst eingestellt sein muss.

## Epson TM-T88V

### 1. Interface-Board prüfen

Der TM-T88V hat ein **austauschbares Interface-Board** (Epson „Connect-It"):

| Board | Anschluss | Für BonBridge |
|---|---|---|
| UB-U03II / UB-U05 / UB-U06 | USB Typ B | ✅ Standardfall |
| UB-S01 | RS-232 (DB25) | ✅ Transport `serial` |
| UB-E04 | Ethernet | ⚠️ Bridge nicht nötig – Kassensystem kann direkt drucken |
| UB-R04 | WLAN | ⚠️ dito |
| UB-P02 | Parallel | ❌ nicht unterstützt |

Das Board sitzt hinten und lässt sich nach Lösen von zwei Schrauben tauschen.

### 2. Selbsttest drucken

Das ist der zuverlässigste Weg, den Ist-Zustand zu sehen:

1. Drucker **ausschalten**
2. **FEED-Taste gedrückt halten**
3. Drucker **einschalten**, FEED weiter halten
4. Loslassen, sobald der Ausdruck startet

Auf dem Ausdruck müssen stehen:

```
INTERFACE  : USB          ← oder Serial, je nach Board
MODE       : ESC/POS      ← WICHTIG
```

Wenn dort etwas anderes steht (z. B. `MODE : Epson Standard` oder ein
OPOS-/Windows-Modus), spricht der Drucker nicht ESC/POS – dann funktioniert
weder BonBridge noch das Kassensystem.

### 3. Modus auf ESC/POS umstellen

Der Modus wird über die **Memory-Switches** gesetzt. Drei Wege:

* **Am Gerät:** Nach dem Selbsttest fragt der Drucker, ob der Setup-Modus
  gestartet werden soll (FEED-Taste kurz drücken). Danach führt ein
  Menü-Ausdruck durch die Einstellungen.
* **Per Software:** ESC/POS-Befehl `GS ( E`. In der BonBridge-Weboberfläche
  unter *Diagnose → Rohdaten senden* kann man ihn absetzen – nur, wenn du
  weißt, was du tust; falsche Memory-Switch-Werte können den Drucker
  unerreichbar machen.
* **Mit Epsons „TM Utility" / „TMFLogo"** von einem Windows-PC.

Nach jeder Änderung: **erneut Selbsttest drucken und prüfen.**

### 4. DIP-Schalter

Beim **USB-Board** sind normalerweise keine DIP-Schalter zu ändern.
Beim **UB-S01 (RS-232)** stellen die DIP-Schalter Baudrate, Datenbits,
Parität und Handshake ein. Werkseinstellung ist meist **38400 8N1, DTR/DSR**.
Die Schalter sitzen unter einer Klappe an der Unterseite; die Belegung steht im
*TM-T88V Technical Reference Guide*.

### 5. Stromversorgung

Der TM-T88V braucht das **Epson PS-180 Netzteil (24 V)**. Der USB-Anschluss
liefert nur die Datenverbindung. Ohne 24 V ist der Drucker für den Rechner
unsichtbar.

### 6. Papier

* 80 mm Rollenbreite: Font A = 42 Zeichen, **Font B = 56 Zeichen**
* 58 mm mit eingelegter Führung: Font A = 32, Font B = 42

Die von BonBridge empfohlenen Werte für den TM-T88V lauten deshalb:

| Einstellung im Kassensystem | Wert |
|---|---|
| Schriftart | `font2` (Font B) |
| Zeichensatz | `cp1252` |
| Zeilenbreite | `56` |

## Epson TM-M244A / TM-m30-Familie

* Meldet sich je nach Firmware **nicht** als USB-Printer-Class →
  `/dev/usb/lp0` erscheint nicht. Das ist normal.
  BonBridge nutzt dann den Transport `usb` (libusb) oder `serial`
  (`/dev/ttyACM0`).
* Umschaltbar zwischen USB / Ethernet / seriell – das Interface muss auf
  **USB** stehen, sonst passiert nichts.
* Ohne 24-V-Netzteil keine USB-Anmeldung.
* Hat eingebautes Netzwerk: Wenn LAN/WLAN genutzt wird, kann OrderAssist
  direkt mit dem Drucker sprechen.

## Generische ESC/POS-Drucker (Munbyn, Zjiang, XPrinter, Equip, Rongta)

| Punkt | Hinweis |
|---|---|
| Papierbreite | 58 mm → 32 Zeichen (Font A), 80 mm → 42 Zeichen |
| Zeichensatz | Für Umlaute und € **cp1252** oder **cp858** wählen |
| Cutter | Viele 58-mm-Geräte haben keinen. In der Weboberfläche unter *Funktionen* abschalten. |
| Kassenlade | Nicht überall vorhanden. Ebenfalls abschaltbar. |
| Selbsttest | Meist ebenfalls „FEED halten beim Einschalten" |

Wenn ein Drucker in der mitgelieferten Datenbank fehlt, wählt BonBridge
automatisch `generic-80mm` oder `generic-58mm`. Das Profil lässt sich in der
Weboberfläche jederzeit manuell umstellen.

## Eigenes Profil anlegen

Profile liegen als YAML unter `/opt/bonbridge/src/bonbridge/profiles/`.
Eine neue Datei anlegen, `bonbridge` neu starten, fertig:

```yaml
id: mein-drucker
name: Mein Bondrucker 80mm
vendor: Beispiel GmbH
based_on: default
width_mm: 80
usb_products:
  - MEINDRUCKER-80
fonts:
  "0": { name: Font A, columns: 42 }
  "1": { name: Font B, columns: 56 }
features:
  paperPartCut: true
  pulseStandard: true
  qrCode: true
codePages:
  "0": CP437
  "16": CP1252
```

Anschließend erkennt BonBridge das Gerät automatisch anhand des
USB-Produktstrings.

## Quellen

* Epson: *TM-T88V Technical Reference Guide* –
  <https://files.support.epson.com/pdf/pos/bulk/tm-t88v_trg_en_revf.pdf>
* Epson: *TM-T88V supported ESC/POS commands* –
  <https://download4.epson.biz/sec_pubs/pos/reference_en/escpos/tmt88v.html>
