# Diagnose und FAQ

## Der schnelle Weg

```bash
bonbridge scan                      # was sieht BonBridge an Hardware?
systemctl status bonbridge          # läuft der Dienst?
journalctl -u bonbridge -n 50       # was sagt das Log?
bonbridge report > bericht.txt      # alles auf einmal
```

Oder in der Weboberfläche: **Diagnose → Support-Bericht herunterladen**.

## Symptomtabelle

### „Der Drucker wird gar nicht gefunden"

| Prüfen | Befehl / Aktion |
|---|---|
| Hat der Drucker sein eigenes 24-V-Netzteil? | Ohne 24 V meldet er sich nicht am USB. Häufigste Ursache. |
| Ist der Pi Zero am richtigen Micro-USB-Port versorgt? | Äußere Buchse = `PWR IN`, innere = `USB` |
| Sieht der Kernel etwas? | `dmesg -w`, dann Drucker neu einstecken |
| Sieht USB etwas? | `lsusb` – bei Epson steht dort `04b8:...` |
| Kabel/Port getauscht? | Anderes USB-Kabel, beim Pi 4 die schwarzen USB-2.0-Ports |
| Steht der Drucker auf dem richtigen Interface? | Selbsttest drucken, `INTERFACE` prüfen – siehe [03](03-drucker-konfiguration.md) |

`dmesg`-Fehler wie `error -71`, `-32` oder `-110` bedeuten fast immer
schlechtes Kabel oder zu schwache Stromversorgung.

### „`/dev/usb/lp0` gibt es nicht"

Das ist bei manchen Modellen **normal** und kein Fehler. Epson TM-M244A und die
TM-m30-Familie melden sich vendor-spezifisch oder als `/dev/ttyACM0`.
BonBridge nutzt dann libusb bzw. den seriellen Transport.

Prüfen:

```bash
bonbridge scan
ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
```

Wenn `bonbridge scan` das Gerät zeigt, ist alles in Ordnung – im Reiter
**Drucker** auf *Geräte suchen* → *Übernehmen* klicken.

### „Verbunden, aber es kommt nichts aus dem Drucker"

1. Weboberfläche → **Diagnose → Letzte Druckaufträge**. Steht der Auftrag da?
   * **Nein** → das Kassensystem hat gar nichts geschickt. IP und
     Netz prüfen: `ping <ip>` vom Handy-Netz aus, gleiches WLAN?
   * **Ja, aber Fehler** → siehe *Letzter Fehler* auf der Übersicht.
2. Direkt testen: **Übersicht → Testseite drucken**. Kommt die Testseite,
   liegt es am Kassensystem, nicht an der Bridge.
3. Von der Kommandozeile:
   ```bash
   printf 'Test\n\n\n' | nc <ip> 9100
   ```

### „Der Ausdruck sieht falsch aus"

| Symptom | Ursache | Lösung |
|---|---|---|
| Zeilen brechen um | Zeilenbreite im Kassensystem zu groß | Wert aus Reiter **Anbindung** übernehmen |
| Umlaute / € falsch | Falsche Codepage | `cp1252` (oder `cp858`) im Kassensystem |
| Alles winzig oder riesig | Falsche Schriftart | `font1` (42 Zeichen) vs. `font2` (56 Zeichen) |
| Papier wird nicht geschnitten | Cutter-Funktion aus oder nicht vorhanden | Reiter **Funktionen** → *Schneiden testen* |
| Schneidet mitten im Text | Kassensystem schneidet selbst **und** BonBridge | Option *Schnitt nach jedem Auftrag* abschalten |

### „Nach einem Neustart geht nichts mehr"

```bash
systemctl status bonbridge
journalctl -u bonbridge -b
```

Häufigste Ursache: Die IP-Adresse des Geräts hat sich geändert (DHCP). Feste
IP im Router reservieren.

### „Der grüne Haken in OrderAssist stimmt nicht"

Der Haken prüft nur, ob eine TCP-Verbindung möglich ist. BonBridge nimmt
Aufträge auch bei leerem Papier entgegen und speichert sie zwischen. Der echte
Zustand steht in der BonBridge-Übersicht.

### „Der Drucker taucht in der OrderAssist-Suche nicht auf"

Das ist erwartetes Verhalten: Die Suche findet laut OrderAssist-Doku nur
EPSON-Netzwerkdrucker. BonBridge wird **manuell über die IP** hinzugefügt.

Es gibt eine **experimentelle** Option, die Epson-Suchpakete zu beantworten
(*System → Epson-Suchprotokoll beantworten*, ENPC auf UDP 3289). Epson
veröffentlicht dieses Protokoll nicht; die Umsetzung beruht auf
Community-Analysen und ist ungetestet. Sie ist standardmäßig **aus**. Wenn sie
nicht funktioniert, ist das kein Fehler – der manuelle Weg bleibt der
unterstützte.

## Statusabfrage verstehen

BonBridge fragt den Drucker regelmäßig mit `DLE EOT` ab. Die vier Gruppen:

| Befehl | Liefert |
|---|---|
| `DLE EOT 1` | Online/Offline, Zustand des Kassenladen-Anschlusses |
| `DLE EOT 2` | Deckel offen, Papiervorschubtaste, Fehlerzustand |
| `DLE EOT 3` | Cutter-Fehler, behebbarer/unbehebbarer Fehler |
| `DLE EOT 4` | Papier fast leer / Papierende |

Das funktioniert nur, weil BonBridge in beide Richtungen mit dem Drucker
spricht. Ein reiner Schreibkanal (wie `socat -u`) kann prinzipbedingt keinen
Status liefern.

Rohwerte stehen in **Diagnose → Status**.

## Zwischenspeicher (Spool)

Wenn der Drucker beim Drucken nicht erreichbar ist, legt BonBridge den Auftrag
unter `/var/lib/bonbridge/spool/<drucker-id>/` ab und versucht es alle fünf
Sekunden erneut. Nach einem Neustart des Dienstes werden gespoolte Aufträge
wieder eingereiht.

Das bedeutet: **Ein Bon geht nicht verloren, wenn kurz das Papier alle ist.**
Wenn er nicht mehr gedruckt werden soll: *Diagnose → Zwischenspeicher leeren*.

## Logs und Dateien

| Pfad | Inhalt |
|---|---|
| `/etc/bonbridge/config.yaml` | Konfiguration |
| `/var/lib/bonbridge/spool/` | zwischengespeicherte Aufträge |
| `/var/log/bonbridge/bonbridge.log` | rotierendes Logfile |
| `journalctl -u bonbridge` | Systemd-Journal |
| `/opt/bonbridge/` | Programmdateien |

Log ausführlicher machen:

```yaml
logging:
  level: DEBUG
```

dann `sudo systemctl restart bonbridge`.

## Ports

| Port | Dienst |
|---|---|
| 9100/tcp | RAW-Druck (Kassensystem) |
| 8080/tcp | Weboberfläche |
| 5353/udp | mDNS (Avahi, optional) |
| 3289/udp | Epson-ENPC-Antwort (experimentell, standardmäßig aus) |
| 631/tcp | CUPS (nur wenn `--with-cups` installiert) |

Prüfen:

```bash
ss -tlnp | grep -E ':(9100|8080|631)'
```

## Neu installieren / aktualisieren

```bash
curl -fsSL https://raw.githubusercontent.com/loe17/Bonbridge/main/install.sh | sudo bash
```

Die Konfiguration bleibt erhalten. Deinstallation:

```bash
sudo bash /opt/bonbridge/uninstall.sh          # Konfiguration bleibt
sudo bash /opt/bonbridge/uninstall.sh --purge  # alles weg
```
