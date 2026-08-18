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

### "The green check mark in OrderAssist is misleading"

It only tests whether a TCP connection is possible. BonBridge accepts jobs
even when the paper is out and spools them. The real state is in the BonBridge
overview.

### "The printer does not show up in the OrderAssist search"

That is expected: according to the OrderAssist documentation the search only
finds EPSON network printers. BonBridge is added **manually by IP**.

There is an **experimental** option to answer Epson discovery probes
(*System → Answer Epson discovery probes*, ENPC on UDP 3289). Epson does not
publish this protocol; the implementation is based on community analysis and
is untested. It is **off** by default. If it does not work, that is not a bug -
the manual route remains the supported one.

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
ss -tlnp | grep -E ':(9100|8080|631)'
```

## Reinstall / update

```bash
curl -fsSL https://raw.githubusercontent.com/loe17/Bonbridge/main/install.sh | sudo bash
```

The configuration is preserved. Uninstall:

```bash
sudo bash /opt/bonbridge/uninstall.sh          # keeps the configuration
sudo bash /opt/bonbridge/uninstall.sh --purge  # removes everything
```
