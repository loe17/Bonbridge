# Epson TM-T88V – USB & ESC/POS Modus prüfen (wichtig!)

## 1) Interface-Modul
Der TM-T88V hat ein austauschbares Interface-Board (UB-Board).
Für USB brauchst du eine Typ-B USB-Buchse (z. B. UB-U05/UB-U03II/UB-U06).

## 2) Self-Test drucken (Kontrolle)
Drucker AUS → FEED gedrückt halten → Drucker EIN → FEED halten bis Ausdruck kommt.
Auf dem Ausdruck prüfen:
- INTERFACE = USB (oder vergleichbar)
- MODE = ESC/POS

## 3) Wenn INTERFACE nicht USB ist
Je nach Board/DIP-Konfiguration muss auf USB umgestellt werden.
Nach Umstellung erneut Self-Test drucken und prüfen.

## 4) Wenn MODE nicht ESC/POS ist
Im Setup/Configuration Menü auf ESC/POS umstellen (modellabhängig).
Danach erneut Self-Test drucken.

## 5) Kontrolle am Raspberry Pi
Nach dem Anstecken muss /dev/usb/lp0 existieren:
```bash
ls /dev/usb/
# -> lp0
dmesg | tail -n 20

