# Connecting OrderAssist and other POS systems

## How OrderAssist addresses printers

From the official OrderAssist documentation:

* Supported are **thermal printers with Wi-Fi or a network connection**.
  **USB and serial are not supported** - which is why BonBridge exists.
* A printer is added by its **IP address**. **The port is fixed at 9100** and
  is not asked for in the app (the OrderAssist test page prints it as
  `192.168.1.20:9100`).
* The automatic printer search only finds **EPSON network printers**.
  Everything else - BonBridge included - is added manually by IP.
* Per printer you configure **font**, **character set** and **line width**.
  The documentation suggests finding the combination by trial and error.
  **BonBridge reads these values out of the printer profile**, so no trial and
  error is needed.
* Printers are assigned to **print groups** (kitchen, bar, …).

## Step by step

### 1. Find the IP address

Open the web interface: `http://<ip>:8080/` or
`http://<hostname>.local:8080/`. The **Overview** tab shows the address to
enter in the POS application.

On the device itself:

```bash
hostname -I
```

> **Tip:** give the BonBridge device a **fixed IP** - either a DHCP
> reservation in the router (easiest) or a static address on the device.
> Otherwise the address will change one day and the POS application will no
> longer find the printer.

### 2. Add the printer in OrderAssist

1. Main menu (☰ top left) → **Drucker**
2. **+ Hinzufügen**
3. The automatic search will not find BonBridge (it looks for EPSON devices) →
   add it **manually**
4. Enter the **IP address**, e.g. `192.168.1.50`. No `http://`, no
   `/printers/...`, no port.
5. Save.

The printer should appear in the list with a **green check mark**.

> **About that check mark:** it means "a TCP connection is possible".
> BonBridge accepts connections even when the receipt printer is out of paper
> or switched off, so that jobs are spooled and printed later instead of being
> lost. **The real printer state is shown in the BonBridge web interface**,
> not by the check mark in the app.

### 3. Set up the print layout

Open the **Integration** tab in the web interface. It shows the concrete
values, e.g. for an Epson TM-T88V with 80 mm paper:

| Field in OrderAssist | Value |
|---|---|
| Schriftart (font) | `font2` |
| Zeichensatz (character set) | `cp1252` |
| Zeilenbreite (line width) | `56` |

Alternatives (also listed in the web interface): `font1` with line width `42`.

### 4. Check the test page

The OrderAssist test page is well designed - check three things:

1. **Line width:** in the ruler (`32:`, `36:`, … `72:`) exactly the line with
   your configured width must reach the edge without wrapping.
2. **Special characters:** `€ ß ä ö ü` must render correctly. If not, the
   character set is wrong - try `cp1252` or `cp858`.
3. **Divider:** the separator line must not wrap onto the next line.

BonBridge has its own, very similar test page: web interface →
**Overview → Print test page**. It additionally shows the device name, IP,
detected model and a QR code pointing at the web interface.

### 5. Assign a print group

In OrderAssist under **Drucker → Ausdruckgruppen definieren**, assign the
printer to the right group. If several physical printers are attached to one
BonBridge device, see [07-print-groups.md](07-print-groups.md).

## Other POS systems

BonBridge behaves like an ordinary network receipt printer (RAW / JetDirect,
port 9100). Anything that can address such a printer works:

| System | Setting |
|---|---|
| Generic "network printer / RAW / socket" | IP + port 9100 |
| URL notation | `socket://<ip>:9100` |
| CUPS / Linux | `lpadmin -p Receipt -E -v socket://<ip>:9100 -m raw` |
| Windows | Add printer → TCP/IP port → device type **RAW**, port 9100 |
| macOS | Add printer → IP → protocol **HP Jetdirect - Socket** |
| Node/Python/PHP | just open a TCP socket on port 9100 and write ESC/POS |

Command line test:

```bash
printf 'Test print\n\n\n' | nc 192.168.1.50 9100
```

## What BonBridge does not do

* **It does not format receipts.** The layout comes entirely from the POS
  application; BonBridge passes the ESC/POS data through unchanged. Optional
  extras (cut, cash drawer) are appended on request.
* **It is not a fiscal memory / TSE.**
* **It does not transcode.** If the POS application sends the wrong code page,
  accented characters print wrong - that is a setting in the app, not in the
  bridge.
