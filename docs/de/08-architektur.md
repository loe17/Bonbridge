# Architektur

![Architektur](../img/architecture.svg)

## Leitgedanke

**Genau ein Prozess besitzt den Drucker.**

Der Vorgänger dieses Projekts hat CUPS und `socat` parallel auf
`/dev/usb/lp0` schreiben lassen. Beide konnten sich gegenseitig in den
ESC/POS-Datenstrom schreiben, und weil `socat -u` unidirektional ist, konnte
niemand feststellen, ob überhaupt etwas gedruckt wurde. BonBridge dreht das um:
Ein Worker-Thread pro Drucker öffnet das Gerät, alle anderen reichen ihm
Aufträge über eine Warteschlange.

## Komponenten

| Modul | Aufgabe |
|---|---|
| `daemon.py` | Setzt alles zusammen, hält den Zustand, beantwortet Anfragen der Web-Schicht |
| `raw_server.py` | TCP-Listener auf Port 9100, ein Listener pro Drucker und IP |
| `jobs.py` | Auftragswarteschlange, Worker-Thread, Spooling, Wiederholung |
| `transports/` | `usb` (libusb), `usblp`, `serial`, `network` |
| `caps.py` | Identifikation und Funktionserkennung |
| `escpos.py` | Befehlskonstanten, Statusdecodierung, Testseiten |
| `web/server.py` | HTTP-Server und REST-API (nur Standardbibliothek) |
| `mdns.py` | Avahi-Servicedatei und optional Zeroconf |
| `discovery.py` | Experimenteller ENPC-Responder (Epson-Suche) |
| `sysinfo.py` | Systeminformationen für Diagnose und Support-Bericht |
| `config.py` | YAML-Konfiguration mit vollständigen Defaults |

## Datenfluss eines Bons

1. OrderAssist öffnet eine TCP-Verbindung zu `<ip>:9100`.
2. `raw_server` liest den Datenstrom. Ein Auftrag endet, wenn die Verbindung
   geschlossen wird **oder** 0,4 s lang nichts mehr kommt. Damit werden sowohl
   „verbinden – senden – trennen" als auch dauerhaft offene Verbindungen
   korrekt behandelt.
3. Der Auftrag geht als `Job` in die Warteschlange des zuständigen Workers.
4. Der Worker stellt sicher, dass der Transport offen ist (bei Bedarf
   Wiederverbindung mit exponentiellem Backoff), schreibt optionale Präambel,
   die Rohdaten und optionale Postambel (Vorschub, Schnitt, Kassenlade).
5. Erfolg: Zähler hoch, Auftrag in der Diagnoseliste, gespoolte Kopie gelöscht.
   Alles, was der Drucker zurückschickt, wird an die ursprüngliche Verbindung
   weitergereicht – so verhält sich auch ein echter JetDirect-Anschluss.
6. Fehler: Auftrag wird gespoolt und nach `retry_seconds` erneut versucht.

## Warum Python und keine Fremdbibliothek für den Webserver

* Python 3 ist auf Raspberry Pi OS und Debian ohnehin installiert.
* `pyusb`, `pyserial` und `PyYAML` gibt es als Debian-Pakete
  (`python3-usb`, `python3-serial`, `python3-yaml`) – kein `pip`, kein
  Compiler, keine virtuelle Umgebung, keine PyPI-Abhängigkeit zur
  Installationszeit.
* Der Webserver baut auf `http.server` auf. Für ein Gerät mit einer Handvoll
  Anfragen pro Minute ist ein Framework unnötiges Gewicht – auf einem Pi Zero
  zählt jede vermiedene Abhängigkeit beim Start.
* Die Weboberfläche ist eine einzige HTML-Datei mit reinem JavaScript. Kein
  Build-Schritt, kein CDN, funktioniert auch ohne Internetzugang.

## Funktionserkennung in vier Stufen

1. **Identität** – USB-Deskriptor (Vendor/Product/Serial), IEEE-1284-Geräte-ID
   aus sysfs, ESC/POS `GS I` (Modell, Typ, ROM-Version).
2. **Profil** – Abgleich gegen die mitgelieferte `escpos-printer-db` (rund 50
   Modelle) und die eigenen Profile unter `profiles/`. Zuordnung über
   USB-Produktstring oder explizite USB-ID.
3. **Live-Status** – `DLE EOT 1..4` liefert Papier, Deckel, Cutter und
   Fehlerzustände. Optional `GS a` (Automatic Status Back).
4. **Aktive Tests** – Cutter, Kassenlade, Signalton. Nur auf Knopfdruck, weil
   sie Papier verbrauchen.

Das Ergebnis ist ein Objekt, in dem jede Funktion drei Werte hat: *erkannt*,
*Überschreibung*, *wirksam*. Die Weboberfläche zeigt alle drei, damit
nachvollziehbar bleibt, woher ein Wert kommt.

## Unabhängigkeit von fremden Repositories

Zur Installation werden nur benötigt:

* das eigene GitHub-Repository (bzw. ein heruntergeladenes Archiv), und
* Debian-Standardpakete.

Zwei Fremdkomponenten liegen **einvendort** im Repo unter `vendor/`:

| Komponente | Lizenz | Wofür |
|---|---|---|
| `zj-58` | BSD-2-Clause | CUPS-Filter, nur für das optionale CUPS-Modul |
| `escpos-printer-db` | CC-BY-4.0 | Modell- und Funktionsdatenbank |

Beide Lizenzen erlauben das Mitliefern. `vendor/*/VENDORED_COMMIT` hält fest,
aus welchem Upstream-Stand die Kopie stammt. Details in `NOTICE`.

Damit gilt: Wenn eines dieser Projekte morgen von GitHub verschwindet, bleibt
BonBridge installierbar und funktionsfähig.

## Sicherheitshinweise

* Die Weboberfläche hat **kein Passwort** (bewusste Entscheidung für ein
  Gerät im lokalen Netz). Port 8080 nicht ins Internet weiterleiten.
* Der Dienst läuft als `root`, weil er direkten USB-Zugriff braucht. Die
  systemd-Unit schränkt ihn mit `NoNewPrivileges`, `ProtectHome` und
  `ReadWritePaths` ein.
* Anders als die alte Lösung wird `/etc/cups/cupsd.conf` **nicht** angefasst.
  CUPS ist optional und bekommt eine eigene Queue, die durch BonBridge druckt.

## Versionierung

* Semantische Versionierung, Git-Tags in der Form `v1.2.3`.
* Ein Tag löst über GitHub Actions ein Release aus, an dem ein
  `bonbridge-<version>.tar.gz` für die Offline-Installation hängt.
* `install.sh` installiert standardmäßig vom `main`-Branch; für eine feste
  Version `--branch v1.2.3` verwenden.
