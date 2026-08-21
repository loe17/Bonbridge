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

Trotzdem soll BonBridge in der Suche auftauchen. Dafür ist zuerst eine
Einsicht nötig:

> **„Gefunden" ist keine Eigenschaft eines Druckers, sondern eines Protokolls.**
> Ein echtes Epson-Netzwerkboard (UB-E04) beantwortet vier verschiedene
> Verfahren, und jede App benutzt ein anderes. Wer nur eines davon bedient, ist
> für die anderen unsichtbar.

BonBridge beantwortet deshalb **alle vier**:

| Protokoll | Port | Wofür Apps es benutzen |
|---|---|---|
| **ENPC** | UDP 3289 | Die Suche des Epson-ePOS-SDK. Broadcast beginnt mit `EPSONQ`, Geräte antworten mit `EPSONq`. |
| **SNMP v1** | UDP 161 | Die verbreitetste Druckersuche überhaupt: das ganze Subnetz mit einer Abfrage nach `sysDescr` durchgehen. Community `public`. |
| **mDNS/Bonjour** | UDP 5353 | Bonjour-Suche über `_pdl-datastream._tcp` und `_printer._tcp`. |
| **LPD/LPR** | TCP 515 | Klassischer Netzwerkdruck; manche Apps prüfen nur, ob der Port offen ist. |

Zusätzlich gibt es **passive Lauschposten** auf IPP (631), ePOS-Device (8008)
und SSDP (1900). Diese antworten bewusst nie – eine halbgare Antwort wäre
schlimmer als keine – aber sie halten fest, wer angeklopft hat.

### Herausfinden, welches Protokoll deine App benutzt

Das ist in einem Versuch geklärt:

1. **Weboberfläche → Diagnose → Automatische Druckersuche** öffnen und
   *Liste leeren* drücken.
2. In der Kassen-App die Druckersuche starten.
3. Die Diagnoseseite neu laden.

In der Protokolltabelle zählt genau die Zeile hoch, die die App benutzt. Jede
einzelne Anfrage steht darunter mit Absender und vollständigem Hexdump.

| Beobachtung | Bedeutung | Nächster Schritt |
|---|---|---|
| Eine Zeile zählt hoch, Drucker erscheint trotzdem nicht | Das Protokoll stimmt, die Antwort passt der App nicht. | Hexdump kopieren und melden – daraus lässt sich das Format nachziehen. Bei ENPC vorher die *Antwortform* umstellen (siehe unten). |
| **Gar nichts** zählt hoch | Die Suchpakete erreichen das Gerät nicht. | Sind Handy und Gerät im selben Netz? Viele Router trennen WLAN-Clients voneinander – „Client Isolation" / „AP Isolation" bzw. Gäste-WLAN abschalten. Broadcasts kommen sonst nie an. |
| Eine Zeile steht auf **„Port belegt"** | Ein anderer Dienst hat den Port. | `ss -ulnp \| grep 3289` bzw. `ss -tlnp \| grep 515`. Häufig: ein installierter `snmpd` auf 161 oder `cupsd` auf 631. |

### Wenn ENPC hochzählt, der Drucker aber nicht erscheint

Das ist der Fall, der am 21.08.2026 gemessen wurde: **7 Anfragen auf UDP 3289,
alle beantwortet, alle anderen Protokolle bei null** — und der Drucker tauchte
trotzdem nicht auf. Damit war die Frage nicht mehr „welches Protokoll?", sondern
nur noch „welches Antwortformat?".

Die Anfrage der App sieht so aus (14 Byte, alle drei Sekunden wiederholt):

```
45 50 53 4f 4e 51  03 00 00 00  00 00 00 00
E  P  S  O  N  Q   Funktion     Länge = 0
```

Ein echter TM-m30 antwortet darauf mit 147 Byte:

```
45 50 53 4f 4e 71  03 00 00 00  00 00 00 85  00 05 01 02 01  "TM-m30" 00 00 …
E  P  S  O  N  q   Funktion     Länge = 133  (unbekannt)      Modell, aufgefüllt
```

Daraus folgen zwei Dinge, die **keine Vermutung** sind:

1. **Das Längenfeld ist Big Endian.** In der Netzwerk-Antwort desselben Geräts
   steht `00 00 00 17`, und es folgen exakt 23 Byte. Little Endian gelesen wäre
   dasselbe Feld 385 875 968.
2. **Den Anfrage-Kopf zu spiegeln kann nicht funktionieren.** Die Anfrage
   deklariert Länge **0**. Eine Antwort, die diesen Kopf spiegelt und dann Daten
   anhängt, sagt dem Client „hier ist nichts" — und ein Parser, der dem
   Längenfeld glaubt, liest gar nicht erst weiter. Genau das war bis
   Version 1.3.0 das Standardverhalten.

### Die Wiederholungen der App als Formatsuche nutzen

Die App wiederholt ihre Suche, bis sie zufrieden ist. Das ist eine kostenlose
Suchschleife: Im Modus **„durchprobieren"** (Standard) bekommt jede Wiederholung
die **nächste** Antwortform, und im Protokoll steht bei jeder Anfrage, welche
verwendet wurde.

Eine einzige Suche testet damit alle Formen durch:

| # | Form | Was sie sendet |
|---|---|---|
| 1 | `device` | Die Antwort eines echten TM-m30, byteweise nachgebaut, nur der Modellname ersetzt |
| 2 | `device+net` | Wie 1, zusätzlich die Netzwerk-Info-Antwort (MAC, IP, Maske, Gateway) |
| 3 | `device-le` | Wie 1, aber Längenfeld Little Endian |
| 4 | `name-padded` | Nur der Modellname, auf 133 Byte aufgefüllt |
| 5 | `name-plain` | Nur der Modellname mit Null-Byte |
| 6 | `identity` | MAC, IP, Maske, Gateway, Modell, Gerätename am Stück |
| 7 | `legacy-echo` | Die alte, nachweislich falsche Fassung — nur zum Vergleich |

**So gehst du vor:**

1. *Liste leeren*, dann in der Kassen-App die Suche starten und **laufen
   lassen**, bis der Drucker erscheint oder die Suche endet.
2. Erscheint der Drucker: Diagnoseseite neu laden und nachsehen, welche Form
   bei der **letzten** Anfrage gesendet wurde.
3. Diese Form unter *ENPC-Antwortform* **fest einstellen** und speichern. Ab
   dann wird immer sie gesendet.

Erscheint der Drucker bei keiner der sieben Formen, schick mir den Hexdump —
mit den echten Anfragebytes und dem Wissen, dass alle sieben ausscheiden, ist
der nächste Schritt sehr viel enger eingegrenzt.

### Hersteller und Modell, die angekündigt werden

Kassen-Apps, die gezielt nach **Epson**-Druckern suchen, filtern nach
Herstellername und Modell. Diese beiden Werte entscheiden also, ob das Gerät in
der Liste überhaupt auftaucht – unabhängig davon, ob die Antwort technisch
ankommt.

Unter *Diagnose → Automatische Druckersuche → Wie sich BonBridge im Netz nennt*:

* **Hersteller** – Standard `EPSON`. Das ist eine Kompatibilitätsangabe, so wie
  ein Browser sich als etwas anderes ausgeben kann, damit eine Seite ihn
  bedient. Im Gerät steckt weiterhin ein Raspberry Pi.
* **Modell** – Standard `auto`: es wird das **tatsächlich erkannte** Modell des
  angeschlossenen Druckers angekündigt (z. B. `TM-T88V`). Nur wenn nichts
  erkannt wurde, greift ein Rückfallwert. Von Hand setzen, wenn die App ein
  bestimmtes Modell erwartet.
* **ENPC-Antwortform** – Epson veröffentlicht das Antwortformat nicht.
  Standard ist *beide senden*: eine gespiegelte und eine strukturierte Antwort
  kurz nacheinander. Clients ignorieren, was sie nicht verstehen. Nur
  umstellen, wenn ein Test etwas anderes nahelegt.

Änderungen wirken sofort – die Lauschposten werden beim Speichern neu
gestartet, ein Dienstneustart ist nicht nötig.

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
| 515/tcp | LPD/LPR – Auffindbarkeit und klassischer Netzwerkdruck |
| 161/udp | SNMP v1 – Standard-Druckersuche, Community `public` |
| 5353/udp | mDNS (Avahi) |
| 3289/udp | Epson-ENPC-Antwort |
| 631/tcp | passiver Lauschposten (IPP) bzw. CUPS, falls installiert |
| 8008/tcp | passiver Lauschposten (Epson ePOS-Device) |
| 1900/udp | passiver Lauschposten (SSDP/UPnP) |

Prüfen:

```bash
ss -tlnp | grep -E ':(9100|8080|515|631)'
ss -ulnp | grep -E ':(161|3289|5353)'
```

## „Der Drucker druckt, aber das Modell wird nicht erkannt"

Steht statt des Modells ein Sammelprofil (`generic-80mm`), sind Zeilenbreite,
Schriftart und Funktionsliste geraten. Ursachen und Abhilfe stehen in
[10-updates.md](10-updates.md#wenn-kein-modell-erkannt-wird). Kurzfassung:
*Neu erkennen* drücken, Anschlussart auf `usb` (libusb) stellen, oder das
Profil von Hand auswählen.

## Netzwerkausfall

Wenn nichts mehr gedruckt wird, ist oft nicht der Drucker schuld, sondern das
Netzwerk. BonBridge druckt dann von sich aus einen Hinweiszettel – siehe
[10-updates.md](10-updates.md#netzwerkberwachung).

## Neu installieren / aktualisieren

```bash
curl -fsSL https://raw.githubusercontent.com/loe17/Bonbridge/main/install.sh | sudo bash
```

Die Konfiguration bleibt erhalten. Deinstallation:

```bash
sudo bash /opt/bonbridge/uninstall.sh          # Konfiguration bleibt
sudo bash /opt/bonbridge/uninstall.sh --purge  # alles weg
```
