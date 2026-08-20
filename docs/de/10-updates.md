# Updates, Netzwerküberwachung und Wartung

## Updates

BonBridge kann sich selbst aktualisieren – über die Konsole oder über die
Weboberfläche. Beide Wege enden im selben `install.sh`; es gibt keinen zweiten
Installationsmechanismus, der auseinanderlaufen könnte.

Angeboten werden **nur veröffentlichte Versionen** (Git-Tags bzw. GitHub-
Releases), nie der bewegliche `main`-Zweig. Was auf einem Gerät landet, ist
also immer etwas, das absichtlich freigegeben wurde.

### Auf der Konsole

```bash
sudo bonbridge update --check     # nur nachsehen, nichts ändern
sudo bonbridge update             # prüfen, Änderungen anzeigen, nachfragen, installieren
sudo bonbridge update -y          # ohne Rückfrage (für Skripte)
```

`bonbridge update` zeigt die installierte und die verfügbare Version, dazu die
Release-Notes, und fragt **einmal** nach. Danach läuft die Installation mit
laufender Ausgabe im Terminal.

### In der Weboberfläche

**System → Updates**. Dort stehen installierte Version, verfügbare Version,
Zeitpunkt der letzten Prüfung und die Änderungen der neuen Version. Der Knopf
*Update installieren* fragt nach und startet dann die Installation; die
Konsolenausgabe läuft live in der Seite mit.

Während des Updates startet der Dienst neu. Die Weboberfläche verliert dabei
kurz die Verbindung – das ist normal, die Seite lädt sich danach selbst neu.
Damit der Neustart des Dienstes die laufende Installation nicht mitreißt, wird
sie unter systemd als **eigene transiente Unit** gestartet
(`systemd-run --unit=bonbridge-update-…`).

> **Sicherheitshinweis.** Die Weboberfläche hat kein Passwort. Wer im selben
> Netz ist, kann damit Software auf dem Gerät installieren. Wenn das nicht
> gewollt ist: **System → Updates → „Updates über die Weboberfläche erlauben"**
> abschalten. Dann geht ein Update nur noch per SSH mit `sudo bonbridge update`.
> In `config.yaml` entspricht das `update.allow_web: false`.

### Update ohne Internet

Manche Geräte stehen bewusst in einem Netz ohne Internetzugang. Dafür gibt es
den Offline-Weg:

1. Auf einem beliebigen Rechner das Release herunterladen –
   `https://github.com/loe17/Bonbridge/releases` → `.tar.gz` oder `.zip`.
2. In der Weboberfläche unter **System → Updates → Update ohne Internet** die
   Datei auswählen und *Datei hochladen und installieren* drücken.

Die Datei wird **vor** der Installation ausgepackt und geprüft: Sie muss
`install.sh`, `src/bonbridge/` und `VERSION` enthalten, und kein Eintrag darf
aus dem Zielordner ausbrechen. Passt etwas nicht, wird sie abgelehnt, bevor
irgendetwas verändert wurde.

Dasselbe auf der Konsole:

```bash
sudo bonbridge update --file /pfad/zu/Bonbridge-1.2.0.tar.gz
```

### Zurückrollen

Vor jedem Update wird die bestehende Installation als Archiv unter
`/var/lib/bonbridge/backups/` gesichert (die letzten drei bleiben liegen).

```bash
sudo bonbridge update --list-backups
sudo bonbridge update --rollback
```

Die Konfiguration in `/etc/bonbridge/` wird von einem Update **nie**
überschrieben. Neue Optionen erscheinen mit ihren Standardwerten.

---

## Netzwerküberwachung

Fällt die Netzwerkverbindung des Geräts aus, hört das Kassensystem einfach auf
zu drucken. Die übliche Diagnose lautet dann „der Drucker ist kaputt" – dabei
ist der Drucker völlig in Ordnung und über USB weiterhin erreichbar.

Genau das nutzt BonBridge: Bei einem Netzwerkausfall **druckt der Drucker einen
Hinweiszettel**, der erklärt, was wirklich los ist und was zu prüfen wäre.

### Was geprüft wird

Alle 60 Sekunden (einstellbar) liest BonBridge direkt aus dem Kernel
(`/sys/class/net`), ob es eine brauchbare Verbindung gibt:

| Zustand | Bedeutung |
|---|---|
| kein Interface | keine Netzwerkkarte vorhanden |
| kein Signal (`carrier`) | LAN-Kabel gezogen oder WLAN nicht verbunden |
| verbunden, keine IP | Kabel steckt, aber DHCP/Router antwortet nicht |
| Gateway antwortet nicht | nur bei aktivierter Gateway-Prüfung |

Es wird kein Hilfsprozess gestartet – wichtig auf kleinen Geräten. Die
zusätzliche **Gateway-Prüfung** (ein Ping auf den Router) erkennt den Fall
„verbunden, aber Router tot", kostet aber pro Prüfung einen Prozess und ist
deshalb standardmäßig aus.

### Wann gedruckt wird

* **Beim Start ohne Netz** – sofort, damit man es merkt, bevor jemand bestellt.
* **Beim Ausfall im Betrieb** – einmal, nicht wiederholt.
* **Beim Wiederverbinden** – mit der aktuellen IP-Adresse, die sich nach einem
  Router-Neustart geändert haben kann.

**Nicht** gedruckt wird, wenn gerade kein Drucker verbunden ist. Ein
zwischengespeicherter Störungszettel, der Tage später aus dem Zusammenhang
gerissen herauskommt, hilft niemandem.

Damit ein kurzer WLAN-Wechsel keinen Zettel produziert, muss der neue Zustand
standardmäßig **zwei aufeinanderfolgende Prüfungen** überstehen
(*Bestätigungen vor der Meldung*).

### Einstellungen

Geräteweit unter **System → Netzwerküberwachung**:

| Einstellung | Standard | Bedeutung |
|---|---|---|
| Netzwerküberwachung aktiv | an | schaltet alles ein/aus |
| Bon bei Ausfall | an | der eigentliche Zweck |
| Bon bei Rückkehr | an | meldet die (evtl. neue) IP |
| Gateway anpingen | aus | erkennt den toten Router |
| Prüfintervall | 60 s | Minimum 10 s |
| Bestätigungen | 2 | Schutz gegen Flattern |

Je Drucker unter **Drucker → Optionen → „Hinweis drucken, wenn das Netzwerk
ausfällt"** (Standard: an). Bei mehreren Druckern lässt sich so festlegen, wer
den Zettel bekommt – meist reicht der Drucker am Tresen.

Mit **Hinweiszettel testen** kann der Ausdruck jederzeit ausprobiert werden,
ohne das Kabel zu ziehen.

---

## Bilder drucken

Unter **Drucken → Bild** lassen sich Bilddateien auf den Bondrucker bringen –
Logos, Hinweisschilder, QR-Plakate.

* Formate: **PNG, JPG, BMP, GIF, WebP**.
* **PDF wird nicht unterstützt.** Ein PDF vorher am Rechner als PNG
  exportieren; BonBridge sagt das auch, wenn man es trotzdem versucht.

Die **Vorschau ist keine Simulation**: Das Gerät rechnet die Datei in genau die
Punkte um, die es drucken würde, und schickt dieses Bitmap als Bild zurück. Ein
Logo, das nach dem Schwellwert zu einem schwarzen Block wird, sieht man also,
bevor es Papier kostet.

| Einstellung | Wirkung |
|---|---|
| Breite (%) | Anteil der Druckbreite; 100 % = volle Breite |
| Graustufen simulieren | Rasterung (Floyd–Steinberg). Für Fotos fast immer richtig |
| Schwellwert | nur ohne Rasterung: ab welcher Helligkeit ein Punkt schwarz wird. Für Logos und Strichzeichnungen meist sauberer |
| Invertieren | tauscht Schwarz und Weiß |

Technisch wird das Bild auf Graustufen reduziert, auf die Punktbreite des
erkannten Druckers skaliert (TM-T88V: 512, die meisten 80-mm-Geräte: 576,
58-mm-Geräte: 384), in 1 Bit umgewandelt und als `GS v 0`-Rasterbild in
Streifen von 128 Zeilen gesendet.

Der Bilddruck braucht das Paket **`python3-pil`**. Der Installer bringt es mit;
fehlt es, sagt die Oberfläche, wie man es nachinstalliert:

```bash
sudo apt install python3-pil
sudo systemctl restart bonbridge
```

---

## Wenn kein Modell erkannt wird

Steht in der Übersicht ein Sammelprofil (`generic-80mm`) statt des Modells,
druckt der Drucker zwar, aber Zeilenbreite, Schriftart und Funktionsliste sind
geraten. Die Statusanzeige meldet das jetzt ausdrücklich und listet auf, welche
Kennungen überhaupt gelesen werden konnten.

BonBridge zieht die Modellkennung aus vier Quellen:

1. dem USB-Herstellerstring,
2. dem USB-Produktstring,
3. der **IEEE-1284-Gerätekennung** (`MFG:EPSON;MDL:TM-T88V;…`) – das ist bei
   Anschluss über `/dev/usb/lpN` oft die einzige Quelle,
4. einer lesbaren Antwort auf `GS I`.

Wenn nichts davon lesbar ist:

* **Neu erkennen** im Reiter *Drucker* drücken.
* Anschlussart auf **`usb` (libusb)** statt `usblp` stellen – libusb liest die
  Deskriptorstrings direkt.
* Notfalls das **Profil von Hand auswählen**. Das ist völlig legitim und wird
  dauerhaft gespeichert.

## Wartung, die sich lohnt

```bash
journalctl -u bonbridge --vacuum-size=20M   # Logs kürzen
bonbridge report > bericht.txt              # alles auf einmal für den Support
ls -la /var/lib/bonbridge/backups/          # was liegt an Rücksprungpunkten bereit
```
