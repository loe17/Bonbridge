# Wiring diagrams

![USB wiring diagram](../img/wiring-usb.svg)

## 1. Standard case: USB

```
   ┌────────────────────┐              ┌──────────────────────────┐
   │  230 V mains       │              │   230 V mains            │
   └─────────┬──────────┘              └───────────┬──────────────┘
             │                                     │
   ┌─────────▼──────────┐              ┌───────────▼──────────────┐
   │ 5 V / 2.5 A PSU    │              │ Epson PS-180  24 V       │
   │ (Pi Zero: Micro-USB│              │ MANDATORY own PSU        │
   │  Pi 4/5: USB-C)    │              │ USB cannot power it      │
   └─────────┬──────────┘              └───────────┬──────────────┘
             │ to the "PWR IN" socket              │ DC plug
   ┌─────────▼───────────────────────┐             │
   │  Raspberry Pi Zero 2 W          │  ┌──────────▼───────────────┐
   │                                 │  │  Epson TM-T88V           │
   │  "USB" socket (inner) ──────────┼──┤  USB type B (UB-U03II)   │
   │        │                        │  │                          │
   │        └─ USB-OTG adapter       │  │  DK socket (RJ11) ───────┼──▶ cash drawer
   │           Micro-USB → USB-A     │  │  MODE must be ESC/POS    │      (optional)
   │           + cable USB-A → USB-B │  └──────────────────────────┘
   │                                 │
   │  Wi-Fi ─────────────────────────┼──▶ router ──▶ tablet/phone (POS app)
   └─────────────────────────────────┘
```

### The three most common mistakes

1. **Power on the wrong socket.** The Pi Zero has two identical looking
   Micro-USB sockets. The **outer** one (closer to the corner) is `PWR IN`,
   the **inner** one is `USB`. Swap them and either the Pi does not boot or
   the printer is never detected.
2. **No 24 V supply on the printer.** Without its own power the printer does
   not enumerate over USB at all - `lsusb` simply shows nothing.
3. **A passive USB hub in between.** Connect directly. If a hub is
   unavoidable, use a powered one.

### Verifying the wiring

```bash
lsusb                    # is the printer visible?
ls /dev/usb/             # is there an lp0? (not for every model, see below)
dmesg | tail -n 20       # what does the kernel say when you plug it in?
bonbridge scan           # what does BonBridge see?
```

> **Important:** a missing `/dev/usb/lp0` does **not** mean something is
> broken. Epson models such as the TM-M244A or the TM-m30 family present a
> vendor specific interface or a `/dev/ttyACM0` port. BonBridge uses libusb in
> that case and works anyway. This is exactly where the old `socat` setup
> failed.

## 2. No Pi needed: printer with a network interface

```
Tablet with POS app ──Wi-Fi──▶ router ──LAN──▶ Epson TM-T88V with UB-E04
                                                port 9100
```

If the printer gets a UB-E04 (Ethernet) or UB-R04 (Wi-Fi) board, no bridge is
required. BonBridge can still run as a pure monitoring device in that case
(transport `network`) to provide status and diagnostics.

## 3. Serial (Epson UB-S01, older printers, ESP32 experiments)

```
   ESP32 / Pi UART (3.3 V)          MAX3232 (3.3 V version!)      UB-S01 (DB25 / DB9)
   TXD  ─────────────────────▶  T1IN   T1OUT ────────────────▶  RXD   (DB9 pin 2)
   RXD  ◀─────────────────────  R1OUT  R1IN  ◀────────────────  TXD   (DB9 pin 3)
   GND  ──────────────────────── GND ─────────────────────────  GND   (DB9 pin 5)
   3.3 V ─────────────────────── VCC
                                 C1..C4 = 100 nF charge pump capacitors
```

* **Never** connect TTL levels directly to RS-232. RS-232 swings ±12 V and
  destroys ESP32 or Pi pins instantly.
* Use the **3.3 V variant** (MAX3232, not the 5 V MAX232).
* Baud rate and handshake must match between the UB-S01 DIP switches and the
  configuration. The Epson factory setting is usually **38400 8N1 with
  DTR/DSR**.
* DB9 vs DB25: the pin numbers above are for DB9. On a DB25 connector it is
  RXD = pin 3, TXD = pin 2, GND = pin 7.

BonBridge configuration:

```yaml
transport:
  type: serial
  device: /dev/ttyS0        # or /dev/ttyUSB0
  baudrate: 38400
  dsrdtr: true
```

## 4. Several printers on one device

Two USB printers on one Pi 4, each with its own IP address on port 9100 - see
[07-print-groups.md](07-print-groups.md).

```
                       ┌── USB ──▶ kitchen printer  (binds to 192.168.1.51:9100)
Pi 4 ──── LAN ─────────┤
                       └── USB ──▶ bar printer      (binds to 192.168.1.52:9100)
```

## 5. Cash drawer

The cash drawer is **not** connected to the Pi but to the printer's `DK`
socket with an RJ11/RJ12 cable. BonBridge fires it with the ESC/POS command
`ESC p` - testable in the web interface under *Features → Open cash drawer*.
