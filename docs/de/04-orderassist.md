# Anbindung an OrderAssist und andere Kassensysteme

## Wie OrderAssist Drucker anspricht

Aus der offiziellen OrderAssist-Dokumentation ergibt sich:

* Unterstützt werden **Thermodrucker mit WLAN oder Netzwerkanschluss**.
  **USB und seriell werden nicht unterstützt** – deshalb gibt es BonBridge.
* Ein Drucker wird über die **IP-Adresse** hinzugefügt. **Der Port ist fest
  9100** und wird in der App nicht abgefragt (auf der OrderAssist-Testseite
  steht er als `192.168.1.20:9100`).
* Die automatische Druckersuche findet **nur EPSON-Netzwerkdrucker**. Alles
  andere – auch BonBridge – wird manuell über die IP eingetragen.
* Pro Drucker werden **Schriftart**, **Zeichensatz** und **Zeilenbreite**
  eingestellt. Die Doku empfiehlt, die Kombination auszuprobieren.
  **BonBridge liest diese Werte aus dem Druckerprofil aus** – Ausprobieren
  entfällt.
* Drucker werden **Ausdruckgruppen** zugewiesen (Küche, Theke …).

## Schritt für Schritt

### 1. IP-Adresse feststellen

Weboberfläche öffnen: `http://<ip>:8080/` oder `http://<hostname>.local:8080/`.
Der Reiter **Übersicht** zeigt die Adresse, die ins Kassensystem gehört.

Alternativ auf dem Gerät:

```bash
hostname -I
```

> **Tipp:** Gib dem BonBridge-Gerät eine **feste IP** – im Router per
> DHCP-Reservierung (einfachster Weg) oder statisch auf dem Gerät. Sonst
> ändert sich die Adresse irgendwann und das Kassensystem findet den Drucker
> nicht mehr.

### 2. Drucker in OrderAssist anlegen

1. Hauptmenü (☰ oben links) → **Drucker**
2. **+ Hinzufügen**
3. Die automatische Suche findet BonBridge nicht (sie sucht EPSON-Geräte) →
   **manuell hinzufügen**
4. **IP-Adresse** eintragen, z. B. `192.168.1.50`. Kein `http://`, kein
   `/printers/...`, keine Portangabe.
5. Speichern.

Der Drucker sollte in der Liste mit **grünem Haken** erscheinen.

> **Zum grünen Haken:** Er bedeutet „TCP-Verbindung möglich". BonBridge nimmt
> Verbindungen auch dann an, wenn der Bondrucker gerade kein Papier hat oder
> ausgeschaltet ist – damit Aufträge zwischengespeichert und später gedruckt
> werden, statt verloren zu gehen. **Der echte Druckerzustand steht in der
> BonBridge-Weboberfläche**, nicht im Haken der App.

### 3. Druckbild einstellen

Reiter **Anbindung** in der Weboberfläche öffnen. Dort stehen die konkreten
Werte, z. B. für einen Epson TM-T88V mit 80-mm-Papier:

| Feld in OrderAssist | Wert |
|---|---|
| Schriftart | `font2` |
| Zeichensatz | `cp1252` |
| Zeilenbreite | `56` |

Alternativen (ebenfalls in der Weboberfläche gelistet): `font1` mit
Zeilenbreite `42`.

### 4. Testseite prüfen

Die OrderAssist-Testseite ist gut gemacht – prüfe drei Dinge:

1. **Zeilenbreite:** Im Lineal (`32:`, `36:`, … `72:`) muss genau die Zeile
   mit deiner eingestellten Breite bis an den Rand reichen, ohne umzubrechen.
2. **Sonderzeichen:** `€ ß ä ö ü` müssen korrekt erscheinen. Wenn nicht, ist
   der Zeichensatz falsch – `cp1252` bzw. `cp858` probieren.
3. **Divider:** Die Trennlinie darf nicht auf die nächste Zeile umbrechen.

BonBridge hat eine eigene, sehr ähnliche Testseite: Weboberfläche →
**Übersicht → Testseite drucken**. Sie zeigt zusätzlich Gerätename, IP,
erkanntes Modell und einen QR-Code auf die Weboberfläche.

### 5. Ausdruckgruppe zuweisen

In OrderAssist unter **Drucker → Ausdruckgruppen definieren** den Drucker der
passenden Gruppe zuordnen. Wenn mehrere physische Drucker an einem
BonBridge-Gerät hängen, siehe [07-ausdruckgruppen.md](07-ausdruckgruppen.md).

## Andere Kassensysteme

BonBridge verhält sich wie ein ganz normaler Netzwerk-Bondrucker
(RAW / JetDirect, Port 9100). Alles, was einen solchen Drucker ansprechen
kann, funktioniert:

| System | Einstellung |
|---|---|
| Allgemein „Netzwerkdrucker / RAW / Socket" | IP + Port 9100 |
| URL-Schreibweise | `socket://<ip>:9100` |
| CUPS / Linux | `lpadmin -p Bon -E -v socket://<ip>:9100 -m raw` |
| Windows | Drucker hinzufügen → TCP/IP-Port → Gerätetyp **RAW**, Port 9100 |
| macOS | Drucker hinzufügen → IP → Protokoll **HP Jetdirect – Socket** |
| Node/Python/PHP | einfach ein TCP-Socket auf Port 9100, ESC/POS hineinschreiben |

Test von der Kommandozeile:

```bash
printf 'Testdruck\n\n\n' | nc 192.168.1.50 9100
```

## Was BonBridge nicht macht

* **Es formatiert keine Bons.** Das Layout kommt vollständig vom
  Kassensystem; BonBridge reicht die ESC/POS-Daten unverändert durch.
  Optionale Zusätze (Schnitt, Kassenlade) hängt es auf Wunsch hinten an.
* **Es ist kein Fiskalspeicher / keine TSE.**
* **Es rechnet nicht um.** Wenn das Kassensystem eine falsche Codepage
  sendet, drucken die Umlaute falsch – das ist eine Einstellung in der App,
  nicht in der Bridge.
