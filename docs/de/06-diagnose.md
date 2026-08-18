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

### „Die Kassenlade wird als vorhanden angezeigt, es ist aber keine da"

Das ist keine Fehlfunktion, sondern eine Grenze der Hardware — und BonBridge
zeigt das jetzt sauber getrennt an:

* **„Kassenlade" in der Funktionsliste** heißt: *Der Drucker hat eine
  Kassenladen-Buchse und kann den Impuls senden.* Beim TM-T88V stimmt das
  immer, auch wenn nichts eingesteckt ist.
* **„Zustand der Kassenlade"** darunter ist die Live-Messung.

Der Drucker meldet nur den **Pegel von Pin 3** der Buchse:

| Messung | Bedeutung |
|---|---|
| Pin **LOW** | Eine Lade ist angeschlossen **und geschlossen** — eindeutig |
| Pin **HIGH** | Lade offen **ODER** keine Lade angeschlossen — elektrisch identisch |

Ein einzelner Messwert kann die beiden HIGH-Fälle also nicht unterscheiden.
Was sie unterscheidet, ist der Verlauf: Wer den Pin schon einmal LOW gesehen
hat, weiß, dass eine Lade existiert. Genau das merkt sich BonBridge dauerhaft
(auch über einen Stromausfall hinweg).

**Aktiver Test:** *Funktionen → Kassenlade prüfen*. Der Test liest den Pin,
löst den Impuls aus und liest erneut. Springt der Pegel von LOW auf HIGH, ist
eine Lade angeschlossen — das kann nichts anderes verursachen. Bleibt er in
beiden Messungen HIGH, ist entweder keine Lade angeschlossen oder sie stand
schon offen.

Wenn du sicher weißt, dass keine Lade angeschlossen ist und die Funktion nicht
angeboten werden soll: *Funktionen → Kassenlade → aus (erzwungen)*.

### „bonbridge.local funktioniert nicht"

Unter Windows ist das normal. Namen mit `.local` werden per mDNS aufgelöst;
macOS, iOS, Android und die meisten Linux-Desktops können das von Haus aus,
**Windows nur mit installiertem Bonjour**.

Das ist kein Problem: **Die IP-Adresse funktioniert überall.** Sie steht auf
dem Statusbon, den BonBridge beim Einschalten druckt. Damit sie stabil bleibt,
im Router eine DHCP-Reservierung für das Gerät eintragen.

### „Der grüne Haken in OrderAssist stimmt nicht"

Der Haken prüft nur, ob eine TCP-Verbindung möglich ist. BonBridge nimmt
Aufträge auch bei leerem Papier entgegen und speichert sie zwischen. Der echte
Zustand steht in der BonBridge-Übersicht.

### „Der Drucker taucht in der automatischen Suche nicht auf"

Der zuverlässige Weg bleibt: **Drucker manuell über die IP-Adresse hinzufügen.**
Die IP steht auf dem Statusbon, den BonBridge beim Einschalten druckt, und in
der Weboberfläche.

Trotzdem versucht BonBridge, in der Suche aufzutauchen. Kassen-Apps suchen
Epson-Drucker über das **ENPC-Protokoll** (UDP 3289): Sie schicken ein
Broadcast-Paket, das mit `EPSONQ` beginnt, Drucker antworten mit `EPSONq`.
BonBridge beantwortet solche Pakete (Standard: an, abschaltbar unter *System*).

**Epson veröffentlicht dieses Protokoll nicht.** Das Antwortformat beruht auf
öffentlichen Analysen Dritter – dass die Antwort korrekt ist, lässt sich ohne
Originalgerät nicht garantieren. Deshalb gibt es die Diagnose:

**Weboberfläche → Diagnose → Automatische Druckersuche**

Dort steht, wie viele Suchanfragen angekommen sind, von welcher Adresse, und
jede einzelne als Hexdump. Das beantwortet die entscheidende Frage in einem
einzigen Versuch:

1. Suche in der Kassen-App starten.
2. In der Diagnose nachsehen.

| Beobachtung | Bedeutung | Nächster Schritt |
|---|---|---|
| **Anfragen erscheinen, Drucker taucht trotzdem nicht auf** | Die Suche erreicht das Gerät, aber unsere Antwort passt nicht. | Hexdump kopieren und melden – daraus lässt sich das Format nachziehen. |
| **Keine Anfragen** | Die App sucht nicht per ENPC (oder das Broadcast kommt nicht durch). | Prüfen, ob Handy und Gerät im selben WLAN sind und ob der Router Broadcasts blockiert (Gäste-WLAN, „Client Isolation" / „AP Isolation" abschalten). Kommt weiterhin nichts an, benutzt die App ein anderes Verfahren – dann ist der manuelle Weg der richtige. |
| **Anfragen erscheinen, „beantwortet" steht auf nein** | Der Responder läuft nicht oder Port 3289 ist belegt. | `ss -ulnp \| grep 3289` prüfen. |

Häufigste Ursache für „keine Anfragen": **Client-Isolation im WLAN**. Viele
Router trennen WLAN-Clients voneinander, dann kommen Broadcasts nie an. Der
Drucker ist dann trotzdem über die IP erreichbar, nur die Suche funktioniert
nicht.

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

## Automatische Ausdrucke

| Ausdruck | Standard | Wo einstellbar |
|---|---|---|
| **Statusbon beim Start** – IP-Adresse, Port, Werte fürs Kassensystem, QR-Code auf die Weboberfläche | **an** | Drucker → Optionen |
| **Papier-fast-leer-Warnung** – einmalig, wenn die Rolle zur Neige geht | aus | Drucker → Optionen |

Der Statusbon ist bewusst voreingestellt: Das Gerät hat keinen Bildschirm, und
ein Zettel mit der IP-Adresse ist der schnellste Weg von „eingesteckt" zu „die
App druckt". Er lässt sich jederzeit erneut anstoßen: *Übersicht → Statusbon
drucken*.

Beide Einstellungen liegen in `/etc/bonbridge/config.yaml` und überstehen
einen Stromausfall. Auch die Information „Warnung wurde bereits gedruckt"
überlebt einen Neustart – nach dem Papierwechsel wird sie automatisch
zurückgesetzt.

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
