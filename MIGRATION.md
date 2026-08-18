# Migration from the old setup

*(Umstieg von der alten Lösung — deutsch weiter unten)*

If you already run the CUPS + `socat` installer from
`OrderAssist-over-Raspberry-Pi-with-Epson-TM-T88V`, this is how to move to
BonBridge. Nothing has to change in the POS application: the printer keeps its
IP address and port 9100.

## English

### 1. Remove the old bridge

```bash
sudo systemctl disable --now socket-9100.service
sudo rm -f /etc/systemd/system/socket-9100.service
sudo systemctl daemon-reload
```

Restore the CUPS configuration the old installer overwrote (it kept a backup):

```bash
ls /etc/cups/cupsd.conf.bak.*
sudo cp /etc/cups/cupsd.conf.bak.<timestamp> /etc/cups/cupsd.conf
sudo systemctl restart cups
```

If you do not need CUPS at all - and for OrderAssist you do not - you can stop
it entirely:

```bash
sudo systemctl disable --now cups cups.socket cups.path
```

Optionally remove the old printer queue:

```bash
sudo lpadmin -x EPSON_TM-T88V
```

### 2. Install BonBridge

```bash
curl -fsSL https://raw.githubusercontent.com/loe17/bonbridge/main/install.sh | sudo bash
```

Add `--with-cups` if you also want to keep printing from desktop computers.

### 3. Check

Open `http://<ip>:8080/`. The printer should be detected automatically. Print
a test page from the **Overview** tab.

### 4. Adjust the POS application

Nothing changes in principle - same IP, same port 9100. But now open the
**Integration** tab and copy the recommended font, character set and line
width into OrderAssist. For a TM-T88V on 80 mm paper that is `font2`,
`cp1252`, `56`.

### What is gone, and why

| Old | New |
|---|---|
| `socat -u TCP-LISTEN:9100 → FILE:/dev/usb/lp0` | BonBridge's own listener, bidirectional, with a queue |
| `zj-58` built from GitHub at install time | vendored in `vendor/zj-58`, only built for the optional CUPS module |
| `/etc/cups/cupsd.conf` overwritten | untouched |
| CUPS mandatory | optional |
| No status, no diagnostics | traffic light, `DLE EOT` status, support report |

The old repository name still works: GitHub redirects
`OrderAssist-over-Raspberry-Pi-with-Epson-TM-T88V` to `bonbridge`.

---

## Deutsch

### 1. Alte Bridge entfernen

```bash
sudo systemctl disable --now socket-9100.service
sudo rm -f /etc/systemd/system/socket-9100.service
sudo systemctl daemon-reload
```

Die vom alten Installer überschriebene CUPS-Konfiguration zurückholen (er hat
ein Backup angelegt):

```bash
ls /etc/cups/cupsd.conf.bak.*
sudo cp /etc/cups/cupsd.conf.bak.<zeitstempel> /etc/cups/cupsd.conf
sudo systemctl restart cups
```

Wenn CUPS gar nicht gebraucht wird – und für OrderAssist wird es nicht
gebraucht – kann es ganz abgeschaltet werden:

```bash
sudo systemctl disable --now cups cups.socket cups.path
```

Alte Druckerwarteschlange optional entfernen:

```bash
sudo lpadmin -x EPSON_TM-T88V
```

### 2. BonBridge installieren

```bash
curl -fsSL https://raw.githubusercontent.com/loe17/bonbridge/main/install.sh | sudo bash
```

Mit `--with-cups`, wenn zusätzlich vom Desktop gedruckt werden soll.

### 3. Prüfen

`http://<ip>:8080/` öffnen. Der Drucker sollte automatisch erkannt werden. Im
Reiter **Übersicht** eine Testseite drucken.

### 4. Kassensystem anpassen

Grundsätzlich ändert sich nichts – gleiche IP, gleicher Port 9100. Neu ist:
Im Reiter **Anbindung** stehen die empfohlenen Werte für Schriftart,
Zeichensatz und Zeilenbreite. Für einen TM-T88V mit 80-mm-Papier sind das
`font2`, `cp1252`, `56`.

### Was wegfällt und warum

| Alt | Neu |
|---|---|
| `socat -u TCP-LISTEN:9100 → FILE:/dev/usb/lp0` | eigener Listener, bidirektional, mit Warteschlange |
| `zj-58` zur Installationszeit von GitHub gebaut | liegt in `vendor/zj-58`, wird nur für das optionale CUPS-Modul gebaut |
| `/etc/cups/cupsd.conf` überschrieben | bleibt unangetastet |
| CUPS zwingend | optional |
| kein Status, keine Diagnose | Statusampel, `DLE EOT`, Support-Bericht |

Der alte Repository-Name funktioniert weiter: GitHub leitet
`OrderAssist-over-Raspberry-Pi-with-Epson-TM-T88V` auf `bonbridge` um.
