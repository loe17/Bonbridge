# Epson TM-T88V setup (moved)

This page has been replaced by the full documentation:

* **Deutsch:** [`../docs/de/03-drucker-konfiguration.md`](../docs/de/03-drucker-konfiguration.md)
* **English:** [`../docs/en/03-printer-setup.md`](../docs/en/03-printer-setup.md)

Short version, unchanged:

1. The TM-T88V needs a **USB interface board** (UB-U03II / UB-U05 / UB-U06).
2. Print the **self test**: printer OFF → hold FEED → printer ON → keep
   holding FEED until it prints.
3. The printout must show `INTERFACE : USB` and `MODE : ESC/POS`.
4. The printer needs its **own 24 V power supply** (PS-180). USB alone will
   not power it and it will not enumerate.
5. On the Pi, check with `lsusb`, `ls /dev/usb/` and `dmesg | tail -n 20` —
   or simply run `bonbridge scan`.

> A missing `/dev/usb/lp0` is not necessarily a fault: some Epson models
> present a vendor specific USB interface. BonBridge handles those through
> libusb.
