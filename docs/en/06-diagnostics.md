# Diagnostics and FAQ

## The quick route

```bash
bonbridge scan                      # what hardware does BonBridge see?
systemctl status bonbridge          # is the service running?
journalctl -u bonbridge -n 50       # what does the log say?
bonbridge report > report.txt       # everything at once
```

Or in the web interface: **Diagnostics → Download support report**.

## Symptom table

### "The printer is not found at all"

| Check | Command / action |
|---|---|
| Does the printer have its own 24 V supply? | Without 24 V it does not enumerate over USB. Most common cause. |
| Is the Pi Zero powered on the right Micro-USB port? | Outer socket = `PWR IN`, inner = `USB` |
| Does the kernel see anything? | `dmesg -w`, then replug the printer |
| Does USB see anything? | `lsusb` - Epson shows up as `04b8:...` |
| Tried another cable/port? | Different USB cable; on the Pi 4 the black USB 2.0 ports |
| Is the printer on the right interface? | Print the self test, check `INTERFACE` - see [03](03-printer-setup.md) |

`dmesg` errors like `error -71`, `-32` or `-110` almost always mean a bad
cable or insufficient power.

### "/dev/usb/lp0 does not exist"

For some models this is **normal** and not an error. The Epson TM-M244A and
the TM-m30 family present a vendor specific interface or a `/dev/ttyACM0`
port. BonBridge then uses libusb or the serial transport.

Check:

```bash
bonbridge scan
ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
```

If `bonbridge scan` shows the device, everything is fine - in the **Printers**
tab click *Scan for devices* → *Use*.

### "Connected, but nothing comes out of the printer"

1. Web interface → **Diagnostics → Recent print jobs**. Is the job listed?
   * **No** → the POS application sent nothing. Check IP and network:
     `ping <ip>` from the phone's network, same Wi-Fi?
   * **Yes, but with an error** → see *Last error* on the overview.
2. Test directly: **Overview → Print test page**. If the test page comes out,
   the problem is in the POS application, not in the bridge.
3. From the command line:
   ```bash
   printf 'Test\n\n\n' | nc <ip> 9100
   ```

### "The printout looks wrong"

| Symptom | Cause | Fix |
|---|---|---|
| Lines wrap | Line width too large in the POS app | Use the value from the **Integration** tab |
| Accents / € wrong | Wrong code page | `cp1252` (or `cp858`) in the POS app |
| Everything tiny or huge | Wrong font | `font1` (42 chars) vs `font2` (56 chars) |
| Paper is not cut | Cutter feature off or absent | **Features** tab → *Test cutter* |
| Cuts through the text | POS app cuts **and** BonBridge cuts | Switch off *cut after job* |

### "Nothing works after a reboot"

```bash
systemctl status bonbridge
journalctl -u bonbridge -b
```

Most common cause: the device's IP address changed (DHCP). Reserve a fixed IP
in the router.

### "The cash drawer is reported as present but there is none"

That is not a malfunction but a limit of the hardware - and BonBridge now shows
the two things separately:

* **"Cash drawer" in the feature list** means: *the printer has a drawer
  connector and can fire the pulse.* On a TM-T88V that is always true, even
  with nothing plugged in.
* **"Cash drawer state"** below it is the live measurement.

The printer only reports the **level of pin 3** of the connector:

| Reading | Meaning |
|---|---|
| Pin **LOW** | A drawer is connected **and closed** - unambiguous |
| Pin **HIGH** | Drawer open **OR** no drawer connected - electrically identical |

A single reading therefore cannot distinguish the two HIGH cases. What does
distinguish them is history: once the pin has been LOW, a drawer exists.
BonBridge remembers exactly that, across a power cut.

**Active test:** *Features → Check cash drawer*. It reads the pin, fires the
pulse and reads again. If the level goes from LOW to HIGH a drawer is
connected - nothing else can cause that. If it stays HIGH in both readings,
either no drawer is attached or it was already open.

If you know for certain that no drawer is attached and the feature should not
be offered: *Features → Cash drawer → off (forced)*.

### "bonbridge.local does not work"

On Windows that is normal. `.local` names are resolved via mDNS; macOS, iOS,
Android and most Linux desktops can do it out of the box, **Windows only with
Bonjour installed**.

It does not matter: **the IP address works everywhere.** It is printed on the
status slip at power-up. To keep it stable, add a DHCP reservation for the
device in the router.

### "The green check mark in OrderAssist is misleading"

It only tests whether a TCP connection is possible. BonBridge accepts jobs
even when the paper is out and spools them. The real state is in the BonBridge
overview.

### "The printer does not show up in the automatic search"

The reliable route stays: **add the printer manually by IP address.** The IP is
on the status slip BonBridge prints at power-on, and in the web interface.

Still, BonBridge should turn up in the search. That starts with one insight:

> **"Found" is not a property of a printer but of a protocol.** A real Epson
> network board (UB-E04) answers four different mechanisms, and every app uses
> a different one. Serving only one of them makes you invisible to the rest.

BonBridge therefore answers **all four**:

| Protocol | Port | What apps use it for |
|---|---|---|
| **ENPC** | UDP 3289 | The Epson ePOS SDK search. The broadcast starts with `EPSONQ`, devices answer with `EPSONq`. |
| **SNMP v1** | UDP 161 | The most common printer discovery of all: sweep the whole subnet with one query for `sysDescr`. Community `public`. |
| **mDNS/Bonjour** | UDP 5353 | Bonjour browsing for `_pdl-datastream._tcp` and `_printer._tcp`. |
| **LPD/LPR** | TCP 515 | Classic network printing; some apps only check whether the port is open. |

On top of that there are **passive listeners** on IPP (631), ePOS-Device (8008)
and SSDP (1900). These deliberately never answer - a half-baked reply would be
worse than none - but they record who knocked.

### Finding out which protocol your app uses

One attempt settles it:

1. Open **web interface -> Diagnostics -> Automatic printer search** and press
   *Clear the list*.
2. Start the printer search in the POS app.
3. Reload the diagnostics page.

Exactly the row the app uses counts up in the protocol table. Every single
request is listed underneath with its sender and a full hexdump.

| Observation | Meaning | Next step |
|---|---|---|
| A row counts up, the printer still does not appear | The protocol is right, the app does not like our reply. | Copy the hexdump and report it - the format can be corrected from it. For ENPC, try switching the *reply shape* first (see below). |
| **Nothing** counts up | The search packets never reach the device. | Are the phone and the device on the same network? Many routers isolate Wi-Fi clients from each other - turn off "client isolation" / "AP isolation" or the guest network. Broadcasts otherwise never arrive. |
| A row says **"port in use"** | Another service holds the port. | `ss -ulnp \| grep 3289` or `ss -tlnp \| grep 515`. Common culprits: an installed `snmpd` on 161 or `cupsd` on 631. |

### The manufacturer and model that are announced

POS apps that search specifically for **Epson** printers filter by manufacturer
name and model. Those two values therefore decide whether the device shows up
in the list at all - independently of whether the reply technically arrives.

Under *Diagnostics -> Automatic printer search -> What BonBridge calls itself*:

* **Manufacturer** - default `EPSON`. This is a compatibility declaration, the
  same way a browser can present itself as something else so that a site serves
  it. There is still a Raspberry Pi inside the box.
* **Model** - default `auto`: the **actually detected** model of the attached
  printer is announced (e.g. `TM-T88V`). A fallback only steps in when nothing
  was detected. Set it by hand if the app expects a particular model.
* **ENPC reply shape** - Epson does not publish the reply format. The default is
  *send both*: a mirrored and a structured reply in quick succession. Clients
  ignore what they do not understand. Only change this if a test suggests
  otherwise.

Changes take effect immediately - saving restarts the listeners, no service
restart needed.

## Understanding the status query

BonBridge polls the printer with `DLE EOT`. The four groups:

| Command | Returns |
|---|---|
| `DLE EOT 1` | Online/offline, state of the drawer kick connector |
| `DLE EOT 2` | Cover open, paper feed button, error state |
| `DLE EOT 3` | Cutter error, recoverable/unrecoverable error |
| `DLE EOT 4` | Paper near end / paper end |

This only works because BonBridge talks to the printer in both directions. A
write-only channel (like `socat -u`) cannot report status by construction.

Raw values are in **Diagnostics → Status**.

## Automatic printouts

| Printout | Default | Where to configure |
|---|---|---|
| **Status slip on start-up** - IP address, port, POS settings, QR code to the web interface | **on** | Printers → Options |
| **Paper-low warning** - printed once when the roll runs out | off | Printers → Options |

The status slip is on by default on purpose: the device has no screen, and a
slip with the IP address is the fastest way from "plugged in" to "the app
prints". It can be triggered again at any time: *Overview → Print status slip*.

Both settings live in `/etc/bonbridge/config.yaml` and survive a power cut. The
fact that the warning has already been printed also survives a reboot - it is
reset automatically once new paper is detected.

## Spooling

If the printer is unreachable at print time, BonBridge stores the job under
`/var/lib/bonbridge/spool/<printer-id>/` and retries every five seconds. After
a service restart spooled jobs are re-queued.

That means **a receipt is not lost when the paper runs out briefly**. If it
should no longer be printed: *Diagnostics → Clear spool*.

## Logs and files

| Path | Content |
|---|---|
| `/etc/bonbridge/config.yaml` | Configuration |
| `/var/lib/bonbridge/spool/` | Spooled jobs |
| `/var/log/bonbridge/bonbridge.log` | Rotating log file |
| `journalctl -u bonbridge` | systemd journal |
| `/opt/bonbridge/` | Program files |

More verbose logging:

```yaml
logging:
  level: DEBUG
```

then `sudo systemctl restart bonbridge`.

## Ports

| Port | Service |
|---|---|
| 9100/tcp | RAW printing (POS) |
| 8080/tcp | Web interface |
| 5353/udp | mDNS (Avahi, optional) |
| 3289/udp | Epson ENPC responder (experimental, off by default) |
| 631/tcp | CUPS (only with `--with-cups`) |

Check:

```bash
ss -tlnp | grep -E ':(9100|8080|515|631)'
ss -ulnp | grep -E ':(161|3289|5353)'
```

## "The printer prints, but the model is not detected"

If a generic profile (`generic-80mm`) is shown instead of the model, line
width, font and feature list are guesses. Causes and remedies are in
[10-updates.md](10-updates.md#when-no-model-is-detected). Short version: press
*Re-detect*, switch the transport to `usb` (libusb), or pick the profile by
hand.

## Network outage

When nothing prints any more, the printer is often not at fault - the network
is. BonBridge prints a notice by itself in that case, see
[10-updates.md](10-updates.md#network-watchdog).

## Reinstall / update

```bash
curl -fsSL https://raw.githubusercontent.com/loe17/Bonbridge/main/install.sh | sudo bash
```

The configuration is preserved. Uninstall:

```bash
sudo bash /opt/bonbridge/uninstall.sh          # keeps the configuration
sudo bash /opt/bonbridge/uninstall.sh --purge  # removes everything
```
