# Several print groups (kitchen, bar, counter)

## The problem

OrderAssist assigns each printer to a **print group**. A printer is identified
there solely by its **IP address** - the port is fixed at 9100 and cannot be
changed.

It follows that **two printers need two IP addresses.** They cannot be told
apart by using two ports on the same IP.

BonBridge therefore offers two routes.

## Route A: one BonBridge device per printer (simple)

Each printer gets its own Pi Zero 2 W. Nothing else to do - every device has
its own IP by nature.

| Pros | Cons |
|---|---|
| Simplest setup | ~50 EUR per printer |
| A failure affects one printer only | More devices, more power supplies |
| Short USB runs to the printer | Several web interfaces |

This is the recommended variant for two or three printers in different places
(the kitchen and the bar are rarely next to each other).

## Route B: one device, several IP addresses (elegant)

A Raspberry Pi 4 (or an x86 machine) serves several USB printers. Each printer
gets an **additional IP address** on the same network interface, and BonBridge
binds its listener to that address only.

```
                      ┌── USB ──▶ kitchen printer  ← 192.168.1.51:9100
Pi 4 ── LAN ──────────┤
 (192.168.1.50)       └── USB ──▶ bar printer      ← 192.168.1.52:9100

  Web interface: http://192.168.1.50:8080/
```

### 1. Choose free IP addresses

The additional addresses must

* be in the same subnet as the device,
* be **outside the router's DHCP range** (otherwise the router will hand them
  to another device eventually),
* not be in use yet.

Check:

```bash
ping -c1 192.168.1.51    # must NOT answer
```

### 2. Create the IP aliases

The installer ships a systemd unit for this. The instance name is
`<interface>-<address>-<prefix>`:

```bash
# find the network interface
ip -o addr show scope global

sudo systemctl enable --now 'bonbridge-ip@eth0-192.168.1.51-24.service'
sudo systemctl enable --now 'bonbridge-ip@eth0-192.168.1.52-24.service'
```

On a Pi Zero 2 W the interface is usually `wlan0`:

```bash
sudo systemctl enable --now 'bonbridge-ip@wlan0-192.168.1.51-24.service'
```

Verify:

```bash
ip -4 -o addr show scope global
```

The aliases survive a reboot because the units are enabled.

### 3. Create the printers in BonBridge

Web interface → **Printers**:

1. **Scan for devices** - both USB printers must appear.
2. First printer: name `Kitchen`, *IP address for port 9100* set to
   `192.168.1.51`, assign the device, save.
3. **Add printer** → name `Bar`, `bind` set to `192.168.1.52`, assign the
   second device, save.

Or directly in `/etc/bonbridge/config.yaml`:

```yaml
printers:
  - id: kitchen
    name: Kitchen
    enabled: true
    bind: 192.168.1.51
    transport:
      type: usb
      vendor_id: 0x04b8
      product_id: 0x0202
      serial: "X3M4820015"      # tells two identical printers apart
    profile: TM-T88V

  - id: bar
    name: Bar
    enabled: true
    bind: 192.168.1.52
    transport:
      type: usb
      vendor_id: 0x04b8
      product_id: 0x0202
      serial: "X3M4820099"
    profile: TM-T88V
```

> **Important with identical printers:** two identical TM-T88V units share the
> same vendor/product ID. To keep the assignment stable the **serial number**
> must be configured. `bonbridge scan` shows it. Without a serial the
> assignment can swap after a reboot.

### 4. Enter them in OrderAssist

| Print group | IP in the POS app |
|---|---|
| Kitchen | `192.168.1.51` |
| Bar | `192.168.1.52` |

Then assign them under **Drucker → Ausdruckgruppen definieren**. Distributing
the orders is done by OrderAssist itself - BonBridge only provides the
printers.

| Pros | Cons |
|---|---|
| One device, one web interface, one update | All printers must be cabled to one place |
| Cheaper from two printers on | If the device fails, all printers stop |
| Shared diagnostics and support report | Requires IP management in the router |

## Mixed operation

One BonBridge device can serve USB printers **and** monitor a network printer
at the same time:

```yaml
  - id: counter
    name: Counter
    bind: 192.168.1.53
    transport:
      type: network
      host: 192.168.1.30    # printer with its own UB-E04
      port: 9100
```

Useful when you want status monitoring, spooling and one shared support report
for the network printers as well. If you do not need that, enter the network
printer directly in the POS application.

## Limits

* **One printer, several groups:** no problem - OrderAssist handles that by
  assigning the same printer to several groups.
* **More than ~4 USB printers on one Pi:** possible, but watch the power
  budget and use a powered USB hub.
* **Different subnets:** IP aliases only work within the same network as the
  POS devices.
