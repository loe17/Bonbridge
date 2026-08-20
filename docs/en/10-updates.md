# Updates, network watchdog and maintenance

## Updates

BonBridge can update itself - from the console or from the web interface. Both
routes end in the same `install.sh`; there is no second installation mechanism
that could drift apart from the first.

Only **published versions** are offered (git tags or GitHub releases), never
the moving `main` branch. What lands on a device is therefore always something
that was deliberately released.

### On the console

```bash
sudo bonbridge update --check     # only look, change nothing
sudo bonbridge update             # check, show the changes, ask, install
sudo bonbridge update -y          # no question asked (for scripts)
```

`bonbridge update` shows the installed and the available version plus the
release notes, and asks **once**. After that the installation runs with live
output in the terminal.

### In the web interface

**System -> Updates**. It shows the installed version, the available version,
when it was last checked and what changed. The *Install the update* button asks
for confirmation and then starts the installation; the console output streams
into the page.

The service restarts during the update, so the web interface briefly loses its
connection - that is expected, and the page reloads itself afterwards. So that
the service restart does not take the running installation down with it, the
installer is started as its **own transient unit** under systemd
(`systemd-run --unit=bonbridge-update-...`).

> **Security note.** The web interface has no password. Anyone on the same
> network can use it to install software on the device. If that is not wanted,
> switch off **System -> Updates -> "Allow updates through the web interface"**.
> Updating is then only possible over SSH with `sudo bonbridge update`. In
> `config.yaml` this is `update.allow_web: false`.

### Updating without internet access

Some devices sit deliberately in a network without internet access. For those
there is the offline route:

1. On any machine, download the release from
   `https://github.com/loe17/Bonbridge/releases` - `.tar.gz` or `.zip`.
2. In the web interface under **System -> Updates -> Update without internet**,
   choose the file and press *Upload the file and install*.

The file is unpacked and checked **before** anything is installed: it must
contain `install.sh`, `src/bonbridge/` and `VERSION`, and no member may escape
the target directory. If anything is off it is rejected before a single file
has been touched.

The same on the console:

```bash
sudo bonbridge update --file /path/to/Bonbridge-1.2.0.tar.gz
```

### Rolling back

Before every update the existing installation is packed into an archive under
`/var/lib/bonbridge/backups/` (the last three are kept).

```bash
sudo bonbridge update --list-backups
sudo bonbridge update --rollback
```

An update **never** overwrites the configuration in `/etc/bonbridge/`. New
options appear with their default values.

---

## Network watchdog

When the device loses its network connection, the POS application simply stops
printing. The usual diagnosis is then "the printer is broken" - while the
printer is perfectly fine and still reachable over USB.

BonBridge uses exactly that: on a network outage **the printer prints a notice**
explaining what is actually wrong and what to check.

### What is checked

Every 60 seconds (configurable) BonBridge reads straight from the kernel
(`/sys/class/net`) whether there is a usable connection:

| State | Meaning |
|---|---|
| no interface | no network adapter present |
| no link (`carrier`) | LAN cable unplugged or Wi-Fi disconnected |
| link up, no IP | cable is in, but DHCP/the router is not answering |
| gateway does not answer | only with the gateway check enabled |

No helper process is started - which matters on small devices. The additional
**gateway check** (one ping to the router) catches "connected but the router is
dead", but costs a process per check and is therefore off by default.

### When something is printed

* **At start-up without a network** - straight away, so it is noticed before
  anyone places an order.
* **On an outage during operation** - once, not repeatedly.
* **On reconnection** - with the current IP address, which may have changed
  after a router restart.

Nothing is printed when **no printer is connected** at that moment. A spooled
fault slip that surfaces days later, out of context, helps nobody.

So that a brief Wi-Fi roam does not produce a slip, the new state has to survive
**two consecutive checks** by default (*confirmations before reporting*).

### Settings

Device-wide under **System -> Network watchdog**:

| Setting | Default | Meaning |
|---|---|---|
| Network watchdog active | on | switches everything on/off |
| Slip on outage | on | the actual point |
| Slip on recovery | on | reports the (possibly new) IP |
| Ping the gateway | off | catches the dead router |
| Check interval | 60 s | minimum 10 s |
| Confirmations | 2 | protection against flapping |

Per printer under **Printers -> Options -> "Print a notice when the network
fails"** (default: on). With several printers this decides who gets the slip -
usually the one at the counter is enough.

**Test the notice slip** tries the printout at any time without pulling a cable.

---

## Printing images

Under **Print -> Image** image files can be sent to the receipt printer - logos,
notices, QR posters.

* Formats: **PNG, JPG, BMP, GIF, WebP**.
* **PDF is not supported.** Export the PDF as a PNG on a computer first;
  BonBridge says so as well if you try anyway.

The **preview is not a simulation**: the device converts the file into exactly
the dots it would print and sends that bitmap back as an image. A logo that
turns into a black block after thresholding is therefore visible before it
costs paper.

| Setting | Effect |
|---|---|
| Width (%) | share of the print width; 100% = full width |
| Simulate grey levels | dithering (Floyd-Steinberg). Almost always right for photos |
| Threshold | without dithering only: the brightness at which a dot turns black. Usually cleaner for logos and line art |
| Invert | swaps black and white |

Technically the image is reduced to greyscale, scaled to the dot width of the
detected printer (TM-T88V: 512, most 80 mm devices: 576, 58 mm devices: 384),
converted to 1 bit and sent as a `GS v 0` raster image in bands of 128 rows.

Image printing needs the **`python3-pil`** package. The installer includes it;
if it is missing the interface says how to add it:

```bash
sudo apt install python3-pil
sudo systemctl restart bonbridge
```

---

## When no model is detected

If the overview shows a generic profile (`generic-80mm`) instead of the model,
the printer still prints, but line width, font and feature list are guesses.
The status display now reports this explicitly and lists which identifiers could
be read at all.

BonBridge takes the model identification from four sources:

1. the USB manufacturer string,
2. the USB product string,
3. the **IEEE-1284 device ID** (`MFG:EPSON;MDL:TM-T88V;...`) - often the only
   source when the printer is reached through `/dev/usb/lpN`,
4. a readable answer to `GS I`.

If none of them is readable:

* Press **Re-detect** in the *Printers* tab.
* Switch the transport to **`usb` (libusb)** instead of `usblp` - libusb reads
  the descriptor strings directly.
* Failing that, **pick the profile by hand**. That is perfectly legitimate and
  is stored permanently.

## Maintenance worth doing

```bash
journalctl -u bonbridge --vacuum-size=20M   # trim the logs
bonbridge report > report.txt               # everything at once for support
ls -la /var/lib/bonbridge/backups/          # which rollback points exist
```
