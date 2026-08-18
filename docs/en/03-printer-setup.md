# Configuring the printer itself

A receipt printer can be wired perfectly and still refuse to print because it
is in the wrong mode. This page covers what has to be set on the device.

## Epson TM-T88V

### 1. Check the interface board

The TM-T88V has an **exchangeable interface board** (Epson "Connect-It"):

| Board | Connection | For BonBridge |
|---|---|---|
| UB-U03II / UB-U05 / UB-U06 | USB type B | ✅ standard case |
| UB-S01 | RS-232 (DB25) | ✅ transport `serial` |
| UB-E04 | Ethernet | ⚠️ no bridge needed - the POS app can print directly |
| UB-R04 | Wi-Fi | ⚠️ same |
| UB-P02 | Parallel | ❌ not supported |

The board sits at the back and can be swapped after removing two screws.

### 2. Print the self test

The most reliable way to see the current state:

1. Switch the printer **off**
2. **Hold the FEED button**
3. Switch the printer **on**, keep holding FEED
4. Release once printing starts

The printout must show:

```
INTERFACE  : USB          ← or Serial, depending on the board
MODE       : ESC/POS      ← IMPORTANT
```

If it says something else (for example `MODE : Epson Standard` or an
OPOS/Windows mode), the printer does not speak ESC/POS - and then neither
BonBridge nor the POS application will work.

### 3. Switching the mode to ESC/POS

The mode lives in the **memory switches**. Three ways:

* **On the device:** after the self test the printer offers to enter setup
  mode (short press of FEED). A printed menu then guides through the settings.
* **By software:** the ESC/POS command `GS ( E`. It can be issued from the
  BonBridge web interface under *Diagnostics → Send raw data* - only if you
  know what you are doing; wrong memory switch values can make the printer
  unreachable.
* **With Epson's "TM Utility" / "TMFLogo"** from a Windows PC.

After every change: **print the self test again and verify.**

### 4. DIP switches

On the **USB board** there is normally nothing to change. On the **UB-S01
(RS-232)** the DIP switches set baud rate, data bits, parity and handshake.
The factory setting is usually **38400 8N1, DTR/DSR**. The switches are under
a flap on the underside; the assignment is documented in the *TM-T88V
Technical Reference Guide*.

### 5. Power

The TM-T88V needs the **Epson PS-180 power supply (24 V)**. USB provides the
data connection only. Without 24 V the printer is invisible to the computer.

### 6. Paper

* 80 mm roll: Font A = 42 characters, **Font B = 56 characters**
* 58 mm with the guide inserted: Font A = 32, Font B = 42

BonBridge therefore recommends these values for a TM-T88V:

| Setting in the POS application | Value |
|---|---|
| Font | `font2` (Font B) |
| Character set | `cp1252` |
| Line width | `56` |

## Epson TM-M244A / TM-m30 family

* Depending on firmware it does **not** present a USB printer class interface,
  so `/dev/usb/lp0` never appears. That is normal. BonBridge then uses the
  `usb` (libusb) transport or `serial` (`/dev/ttyACM0`).
* Switchable between USB / Ethernet / serial - the interface must be set to
  **USB**, otherwise nothing happens.
* No 24 V supply means no USB enumeration.
* Has built-in networking: when LAN/Wi-Fi is used, the POS application can
  talk to the printer directly.

## Generic ESC/POS printers (Munbyn, Zjiang, XPrinter, Equip, Rongta)

| Item | Note |
|---|---|
| Paper width | 58 mm → 32 characters (Font A), 80 mm → 42 characters |
| Character set | For accented characters and € choose **cp1252** or **cp858** |
| Cutter | Many 58 mm units have none. Switch the feature off in the web interface. |
| Cash drawer | Not present everywhere. Also switchable. |
| Self test | Usually also "hold FEED while switching on" |

If a printer is missing from the bundled database, BonBridge falls back to
`generic-80mm` or `generic-58mm`. The profile can be changed manually in the
web interface at any time.

## Adding your own profile

Profiles are YAML files under `/opt/bonbridge/src/bonbridge/profiles/`. Create
a new file, restart `bonbridge`, done:

```yaml
id: my-printer
name: My 80mm receipt printer
vendor: Example Ltd
based_on: default
width_mm: 80
usb_products:
  - MYPRINTER-80
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

BonBridge then identifies the device automatically from its USB product
string.

## Sources

* Epson: *TM-T88V Technical Reference Guide* -
  <https://files.support.epson.com/pdf/pos/bulk/tm-t88v_trg_en_revf.pdf>
* Epson: *TM-T88V supported ESC/POS commands* -
  <https://download4.epson.biz/sec_pubs/pos/reference_en/escpos/tmt88v.html>
