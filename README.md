# OrderAssist over Raspberry Pi with Epson TM-T88V

Raspberry Pi OS Lite Printserver für ESC/POS (Epson TM-T88V) mit:
- **CUPS** (Web UI im LAN)
- **zj-58** Treiber (ZJ-80 / ESC/POS)
- **RAW Port 9100** via **socat** für Apps wie **OrderAssist** (RAW/Socket)

## Vorher am Drucker prüfen
Der Epson TM-T88V muss auf **USB Interface** und **ESC/POS Mode** stehen.  
Siehe: `assets/tm-t88v-setup.md`

---

## One-Command Installation (Raspberry Pi)
```bash
sudo apt update && sudo apt install -y git && \
git clone https://github.com/loe17/OrderAssist-over-Raspberry-Pi-with-Epson-TM-T88V.git && \
cd OrderAssist-over-Raspberry-Pi-with-Epson-TM-T88V && \
sudo bash install.sh
