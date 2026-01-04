\# OrderAssist over Raspberry Pi with Epson TM-T88V



Ziel: Raspberry Pi OS Lite als Printserver für ESC/POS (Epson TM-T88V) mit:

\- \*\*CUPS\*\* (Web UI im LAN)

\- \*\*zj-58\*\* Treiber (ZJ-80 / ESC/POS)

\- \*\*RAW Port 9100\*\* via \*\*socat\*\* für Apps wie \*\*OrderAssist\*\* (die oft RAW/Socket erwarten)



\## Vorher am Drucker prüfen

Der Epson TM-T88V muss auf \*\*USB Interface\*\* und \*\*ESC/POS Mode\*\* stehen.

Siehe: `assets/tm-t88v-setup.md`



---



\## Installation auf dem Raspberry Pi (SSH)



\### 1) Repo klonen (SSH)

```bash

sudo apt update \&\& sudo apt install -y git

git clone git clone https://github.com/loe17/OrderAssist-over-Raspberry-Pi-with-Epson-TM-T88V.git

cd OrderAssist-over-Raspberry-Pi-with-Epson-TM-T88V


sudo apt update && sudo apt install -y git && \
git clone https://github.com/DEINUSERNAME/OrderAssist-over-Raspberry-Pi-with-Epson-TM-T88V.git && \
cd OrderAssist-over-Raspberry-Pi-with-Epson-TM-T88V && \
sudo bash install.sh




