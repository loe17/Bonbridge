# Weboberfläche

Erreichbar unter **`http://<ip>:8080/`**.

> Zusätzlich wird der Name `<hostname>.local` per mDNS angekündigt. Das
> funktioniert auf macOS, iOS, Android und den meisten Linux-Desktops, unter
> **Windows aber nur mit installiertem Bonjour**. Verlass dich deshalb auf die
> IP-Adresse – sie funktioniert überall. Der Name ist Komfort, keine
> Voraussetzung.

Die Oberfläche ist **bewusst ohne Passwort** und für das lokale Netz gedacht.
Port 8080 darf nicht ins Internet weitergeleitet werden. Sprache oben rechts
umschaltbar (DE/EN).

## Übersicht

Zeigt zuerst den **Gerätestatus** und darunter pro Drucker eine Statusampel.

Unter jeder Ampel steht ein aufklappbarer Punkt **„Warum? Alle Einzelprüfungen
anzeigen"**. Dort steht jede Prüfung einzeln mit eigener Ampel und einer
Erklärung, was zu tun ist – Unterspannung, CPU-Temperatur, freier Speicher,
fehlende Python-Module, Zustand des Netzwerk-Listeners, Papier, Deckel,
Zwischenspeicher. Eine gelbe Ampel ohne Begründung gibt es damit nicht mehr.

Die Ampel bedeutet:

| Farbe | Bedeutung |
|---|---|
| 🟢 grün | Betriebsbereit |
| 🟡 gelb | Warnung, z. B. Papier fast leer |
| 🔴 rot | Fehler: Papierende, Deckel offen, Cutter-Fehler, oder nicht verbunden |
| ⚪ grau | Status unbekannt (Transport ohne Rückkanal) |

Dazu: die Adresse fürs Kassensystem (anklickbar zum Kopieren), Verbindung,
erkanntes Modell, Auftragszähler, letzter Auftrag, letzter Fehler und der
Zustand des Netzwerk-Listeners.

Die Seite aktualisiert sich alle fünf Sekunden selbst.

## Drucker

Verwaltung der Drucker-Einträge.

* **Geräte suchen** – listet alle USB-, `usblp`- und seriellen Geräte, die als
  Bondrucker in Frage kommen. Mit *Übernehmen* wird ein Gerät einem Drucker
  zugeordnet.
* **Name** – frei wählbar, taucht in Testdrucken und im Support-Bericht auf.
* **IP-Adresse für Port 9100** (`bind`) – siehe den eigenen Abschnitt weiter
  unten. Kurz: bei einem Drucker `0.0.0.0` stehen lassen.
* **Anschluss** – `auto`, `usb`, `usblp`, `serial` oder `network`. `auto` sucht
  bei jedem Start das plausibelste lokale Gerät.
* **Druckerprofil** – `automatisch` oder ein konkretes Modell aus der
  mitgelieferten Datenbank.
* **Optionen** – siehe Tabelle unten.

Änderungen werden sofort übernommen; die betroffenen Listener starten neu.
Jedes Eingabefeld hat eine Erklärung, die beim Darüberfahren mit der Maus
erscheint.

### Optionen je Drucker

| Option | Standard | Wirkung |
|---|---|---|
| **Statusbon beim Start drucken** | **an** | Druckt direkt nach dem Einschalten einen Bon mit IP-Adresse, Port und den Werten fürs Kassensystem. Das Gerät hat keinen Bildschirm – der Zettel ist der schnellste Weg zur IP. Die Einstellung liegt in `config.yaml` und überlebt einen Stromausfall. |
| **Warnung bei Papierende** | aus | Sobald der Drucker „Papier fast leer" meldet, wird **einmalig** ein Hinweiszettel gedruckt. Er wird erst wieder gedruckt, nachdem zwischendurch neues Papier erkannt wurde. Auch dieser Zustand überlebt einen Neustart. |
| Nach jedem Auftrag schneiden | aus | Nur einschalten, wenn das Kassensystem nicht selbst schneidet – sonst wird zweimal geschnitten. |
| Nach jedem Auftrag Kassenlade öffnen | aus | Für Küchendrucker meist unerwünscht. |
| Vor jedem Auftrag zurücksetzen (`ESC @`) | aus | Hilft, wenn ein vorheriger Auftrag Schriftgröße oder Ausrichtung verstellt hinterlässt. |
| Statusabfrage aktiv | an | Ohne sie bleibt die Ampel grau. |
| Abfrageintervall | 10 s | Kleinere Werte belasten den Drucker unnötig. |
| Zeilenvorschub nach Auftrag | 0 | Zusätzliche Leerzeilen vor dem Schnitt. |

### „IP-Adresse für Port 9100" – wofür ist das da?

Dieses Feld bestimmt, **an welche IP-Adresse dieses Geräts** der Druckerport
9100 gebunden wird.

**`0.0.0.0` (Standard) = alle Adressen des Geräts.** Das Kassensystem erreicht
den Drucker dann unter jeder IP, die der Pi hat – über LAN, über WLAN, und auch
noch, wenn sich die Adresse per DHCP ändert. **Bei einem einzigen Drucker ist
das immer die richtige Einstellung. Dann musst du hier nichts anfassen.**

Eine **feste IP** trägst du nur in einem Fall ein: wenn **mehrere Drucker an
diesem einen Gerät** hängen. Der Grund liegt im Kassensystem, nicht in
BonBridge: OrderAssist (und die meisten anderen) identifizieren einen Drucker
**ausschließlich über die IP-Adresse**, der Port ist fest 9100 und lässt sich
in der App nicht ändern. Zwei Drucker unter derselben IP wären für die App
derselbe Drucker.

Die Lösung: Das Gerät bekommt eine zweite (dritte, …) IP-Adresse, und jeder
Drucker lauscht nur auf seiner eigenen:

```
Pi 4, eine Netzwerkkarte, zwei USB-Drucker
  192.168.1.50   Weboberfläche  (Haupt-IP des Geräts)
  192.168.1.51   Drucker Küche  -> Port 9100
  192.168.1.52   Drucker Theke  -> Port 9100
```

Wichtig: Die zusätzliche IP muss vorher **auf dem Gerät angelegt** werden,
sonst kann der Listener nicht starten (die Übersicht zeigt dann einen roten
Netzwerk-Listener mit genau dieser Begründung). Wie das geht, steht in
[07-ausdruckgruppen.md](07-ausdruckgruppen.md).

Weitere sinnvolle Fälle für eine feste Bindung:

* **Nur ein Netz bedienen:** Hängt das Gerät gleichzeitig im LAN und im WLAN
  und soll nur über eine der beiden Strecken drucken, trägst du hier die
  Adresse der gewünschten Schnittstelle ein.
* **Absicherung:** Mit einer festen Bindung nimmt der Drucker keine Aufträge
  über andere Netze des Geräts an.

## Funktionen

Die Funktionsmatrix je Drucker. Jede Zeile zeigt:

* **erkannt** – was aus Profil und Live-Abfrage ermittelt wurde
* **Einstellung** – `automatisch` / `ein (erzwungen)` / `aus (erzwungen)`
* **wirksam** – was BonBridge tatsächlich benutzt

Erkannte Funktionen sind: Papierschneider, Kassenlade, Signalton, Barcodes,
QR-Codes, PDF417, Bilddruck, NV-Logo und Statusabfrage.

**Warum überschreiben?** Die Modell-Datenbank ist eine Sammlung von
Erfahrungswerten. Wenn dein Gerät zwar als „hat Cutter" geführt wird, aber
keinen hat (Baureihenvariante, ausgebauter Cutter), schaltest du die Funktion
hier ab – dann sendet BonBridge keinen Schnittbefehl mehr.

Darunter stehen die **empfohlenen Werte fürs Kassensystem** und die
**aktiven Tests**:

| Test | Wirkung |
|---|---|
| Schneiden testen | Papiervorschub + Teilschnitt |
| Kassenlade öffnen | `ESC p` – Schublade muss aufspringen |
| Signalton | `ESC ( A` – nur bei Geräten mit Buzzer |
| Papiervorschub | vier Zeilen |
| Funktionstestseite | Fett, doppelte Größe, Barcode, QR |

Diese Tests verbrauchen Papier und laufen deshalb nie automatisch.

## Drucken

Ein vollständiger Bon-Editor mit **Live-Vorschau**. Links wird der Bon
zusammengestellt, rechts erscheint sofort, wie er auf dem Papier aussehen wird –
in der echten Zeilenbreite des erkannten Druckers.

| Feld | Bedeutung |
|---|---|
| Drucker | An welchen Drucker der Bon geht |
| Überschrift | Große, fette Zeile ganz oben (optional) |
| Inhalt | Eine Zeile hier = eine Zeile auf dem Bon |
| Fußzeile | Kleiner, zentrierter Text am Ende |
| QR-Code | Wird unten als QR gedruckt (optional) |
| Am Ende schneiden | Nur wirksam, wenn der Drucker einen Schneider hat |
| Kassenlade öffnen | Löst nach dem Druck den Impuls aus |

Zwei Abkürzungen im Inhaltsfeld:

* Eine Zeile, die nur `---` enthält, wird zu einer **Trennlinie**.
* `Text | Wert` setzt den Wert **rechtsbündig** – genau richtig für Preise:

  ```
  2x Cola 0,4l | 7,00
  1x Pommes    | 3,50
  ---
  Summe        | 15,40
  ```

Die Vorschau kommt aus derselben Funktion, die auch die Druckdaten erzeugt –
was du siehst, wird gedruckt. Kann der Drucker etwas nicht (kein Schneider,
kein QR-Code), steht das als Hinweis unter der Vorschau und der entsprechende
Befehl wird weggelassen, statt einen Fehler zu erzeugen.

Wofür das gut ist: Testbons ohne Kassensystem, Beschriftungen, Übergabezettel,
Tagesabschluss-Notizen – und vor allem zum Prüfen, ob Zeilenbreite und
Zeichensatz stimmen, bevor man das Kassensystem konfiguriert.

### Bild drucken

Über den Umschalter **Text | Bild** lassen sich PNG-, JPG-, BMP-, GIF- und
WebP-Dateien drucken. Die Vorschau zeigt das tatsächliche Punktmuster, nicht
eine Annäherung. PDF wird nicht unterstützt. Einzelheiten in
[10-updates.md](10-updates.md).

## Diagnose

* **Letzte Druckaufträge** – Nummer, Quelle (IP des Kassensystems), Größe,
  Zeitpunkt und eine lesbare Vorschau der Daten. Damit lässt sich beantworten:
  *Ist der Auftrag überhaupt angekommen?*
* **Rohdaten senden** – Text oder Hex-Bytes direkt an den Drucker,
  z. B. `1B 40` für `ESC @` (Reset). Für Fehlersuche und Memory-Switches.
* **Zwischenspeicher leeren** – verwirft gespoolte Aufträge, die nicht mehr
  gedruckt werden sollen.
* **Status / Identity** – die rohen Antworten von `DLE EOT` und `GS I`.
* **Alle Prüfungen** – jede einzelne Gesundheitsprüfung von Gerät und Druckern
  mit Begründung. Das ist die Antwort auf „warum steht da eine Warnung?".
* **Automatische Druckersuche** – ob mDNS und der Epson-Suchdienst laufen und,
  am wichtigsten: **welche Suchanfragen tatsächlich angekommen sind**, jeweils
  mit Hexdump. Siehe [06-diagnose.md](06-diagnose.md).
* **Systemausgaben** – `lsusb`, `/dev/usb/`, `ss -tlnp`, `ip addr`,
  `dmesg | tail`, Kernelmodule, Dienststatus.
* **Support-Bericht herunterladen** – eine Textdatei mit allem oben Genannten.
  Das ist die Datei, die man an eine Support-Anfrage anhängt.

## Anbindung

Fertige, kopierbare Einrichtungsanleitung – siehe
[04-orderassist.md](04-orderassist.md). Enthält die IP zum Anklicken, die
empfohlenen Druckeinstellungen, eine nummerierte Schrittliste und
Beispielbefehle für CUPS, Windows, macOS und die Kommandozeile.

## System

* Gerätebezeichnung, Port der Weboberfläche, RAW-Port
* mDNS/Bonjour-Ankündigung an/aus
* Auf die Epson-Druckersuche antworten (ENPC, UDP 3289) – standardmäßig an,
  siehe [06-diagnose.md](06-diagnose.md)
* Suchanfragen protokollieren – damit lässt sich prüfen, ob die Kassen-App
  überhaupt sucht
* Systeminformationen: Modell, Betriebssystem, Kernel, Architektur, Python,
  Laufzeit, freier Speicher
* **Netzwerküberwachung** – Zustand aller Schnittstellen, Prüfintervall und ob
  bei einem Ausfall ein Hinweiszettel gedruckt wird
  (siehe [10-updates.md](10-updates.md))
* **Updates** – installierte und verfügbare Version, Installation mit
  Konsolenausgabe, Upload einer Datei für Geräte ohne Internet, Backups
  (siehe [10-updates.md](10-updates.md))
* Links auf die Dokumentation in der eingestellten Sprache

### Klapp-Zustände bleiben erhalten

Aufgeklappte oder zugeklappte Bereiche (Einzelprüfungen, Hexdumps,
Kommandoausgaben) bleiben so, wie du sie gelassen hast – auch über die
automatische Aktualisierung alle fünf Sekunden und über einen Seitenneuladen
hinweg. Ebenso pausiert die automatische Aktualisierung, solange ein Feld
ungespeicherte Änderungen enthält; sonst würde sie sie überschreiben.

## REST-API

Die Oberfläche benutzt ausschließlich diese API – man kann sie also auch von
einem Skript oder einem Monitoring-System ansprechen.

| Methode | Pfad | Zweck |
|---|---|---|
| GET | `/api/overview` | Gesamtstatus |
| GET | `/healthz` | Lebenszeichen für Monitoring |
| GET/PUT | `/api/config` | Konfiguration lesen/ändern |
| GET/POST | `/api/printers` | Drucker auflisten/anlegen |
| GET/PATCH/DELETE | `/api/printers/<id>` | Drucker lesen/ändern/löschen |
| POST | `/api/printers/<id>/test` | Testdruck (`kind`: `standard`, `features`, `minimal`) |
| POST | `/api/printers/<id>/probe` | `what`: `cut`, `drawer`, `buzzer`, `feed` |
| POST | `/api/printers/<id>/raw` | `{"hex": "1B40"}` oder `{"text": "..."}` |
| POST | `/api/printers/<id>/refresh` | Status neu abfragen |
| POST | `/api/printers/<id>/redetect` | Verbindung + Erkennung neu aufbauen |
| GET | `/api/printers/<id>/integration` | Werte fürs Kassensystem |
| GET | `/api/scan` | Geräte suchen |
| GET | `/api/profiles` | verfügbare Druckerprofile |
| GET | `/api/diagnostics` | Systeminfos + Kommandoausgaben |
| GET | `/api/report` | Support-Bericht als Text |
| POST | `/api/restart` | Drucker und Listener neu starten |
| GET | `/api/network` | Zustand der Netzwerkverbindung |
| POST | `/api/network/check` | Netzwerk sofort prüfen |
| POST | `/api/printers/<id>/network-test` | Hinweiszettel testweise drucken |
| GET | `/api/update` | Update-Status (installiert/verfügbar/Backups) |
| POST | `/api/update/check` | bei GitHub nachfragen |
| POST | `/api/update/install` | `{"source": "online"}` oder `{"source": "file", "file": "..."}` |
| POST | `/api/update/upload` | Archiv hochladen (roher Datei-Inhalt, `?name=`) |
| GET | `/api/update/log` | Konsolenausgabe des laufenden Updates |
| GET | `/api/image/support` | ist der Bilddruck verfügbar? |
| POST | `/api/printers/<id>/image` | Bild hochladen, liefert Vorschau + Token |
| POST | `/api/printers/<id>/image/print` | `{"token": "..."}` drucken |
| GET | `/api/health` | Alle Einzelprüfungen mit Begründung |
| GET | `/api/discovery` | Zustand und Protokoll der automatischen Suche |
| POST | `/api/discovery/clear` | Suchanfragen-Protokoll leeren |
| POST | `/api/printers/<id>/compose` | Bon bauen: `{"spec": …, "print": false}` liefert die Vorschau |
| POST | `/api/printers/<id>/drawer-check` | Aktiver Kassenladen-Test |
| POST | `/api/printers/<id>/startup-report` | Statusbon erneut drucken |
| GET | `/docs`, `/docs/de/<datei>.md` | Dokumentation als HTML |

Beispiel:

```bash
curl -s http://192.168.1.50:8080/api/overview | python3 -m json.tool
curl -s -X POST http://192.168.1.50:8080/api/printers/printer1/test \
     -H 'Content-Type: application/json' -d '{"kind":"standard"}'
```
