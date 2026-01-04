bash
#!/usr/bin/env bash
set -euo pipefail

# ====== Einstellungen (optional überschreibbar) ======
PRINTER_NAME="${PRINTER_NAME:-EPSON_TM-T88V}"
USB_DEVICE="${USB_DEVICE:-/dev/usb/lp0}"
ENABLE_AVAHI="${ENABLE_AVAHI:-1}"
# ====================================================

if [[ $EUID -ne 0 ]]; then
  echo "Bitte als root ausführen: sudo bash install.sh"
  exit 1
fi

echo "== Installer: CUPS + zj-58 + socat(9100) =="
echo "Printer name: ${PRINTER_NAME}"
echo "USB device:   ${USB_DEVICE}"
echo

echo "== Pakete installieren =="
apt update
apt install -y \
  cups socat git build-essential cmake libcups2-dev libcupsimage2-dev \
  cups-filters ghostscript net-tools

if [[ "${ENABLE_AVAHI}" == "1" ]]; then
  apt install -y avahi-daemon
  systemctl enable --now avahi-daemon || true
fi

echo "== USB Device prüfen =="
modprobe usblp || true
if [[ ! -e "${USB_DEVICE}" ]]; then
  echo "FEHLER: ${USB_DEVICE} nicht gefunden."
  echo "Tipp: ls /dev/usb/  und  dmesg | tail -n 30"
  exit 2
fi

echo "== CUPS klassisch starten (ohne socket activation) =="
systemctl disable --now cups.socket cups.path 2>/dev/null || true
systemctl enable --now cups

echo "== cupsd.conf (LAN-freundlich) setzen =="
CUPSD_CONF="/etc/cups/cupsd.conf"
cp "${CUPSD_CONF}" "/etc/cups/cupsd.conf.bak.$(date +%Y%m%d_%H%M%S)"

cat > "${CUPSD_CONF}" <<'EOF'
Listen /run/cups/cups.sock
Listen 0.0.0.0:631
Listen [::]:631

LogLevel warn
PageLogFormat
Browsing On
BrowseLocalProtocols dnssd
WebInterface Yes
DefaultAuthType None
DefaultEncryption Never
IdleExitTimeout 60

<Location />
  Order allow,deny
  Allow all
</Location>

<Location /admin>
  AuthType Default
  Order allow,deny
  Allow all
  Require user @SYSTEM
</Location>

<Location /admin/conf>
  AuthType Default
  Order allow,deny
  Allow all
  Require user @SYSTEM
</Location>

<Location /printers>
  Order allow,deny
  Allow all
</Location>
EOF

cupsd -t
systemctl restart cups

echo "== zj-58 Treiber installieren (ESC/POS / ZJ-80) =="
WORKDIR="/opt/rpi-escpos-printserver"
mkdir -p "${WORKDIR}"

if [[ ! -d "${WORKDIR}/zj-58" ]]; then
  git clone https://github.com/klirichek/zj-58.git "${WORKDIR}/zj-58"
else
  (cd "${WORKDIR}/zj-58" && git pull --ff-only)
fi

mkdir -p "${WORKDIR}/zj-58/build"
cd "${WORKDIR}/zj-58/build"
cmake ..
make -j"$(nproc)"
make install
systemctl restart cups

echo "== CUPS Druckerqueue anlegen (best effort) =="
USB_URI="$(lpinfo -v 2>/dev/null | awk '/usb:\/\/EPSON\/TM-T88V/ {print $2; exit}' || true)"
if [[ -z "${USB_URI}" ]]; then
  USB_URI="usb://EPSON/TM-T88V"
fi

MODEL="$(lpinfo -m 2>/dev/null | awk 'tolower($0) ~ /zj-80/ {print $1; exit}' || true)"
if [[ -z "${MODEL}" ]]; then
  MODEL="raw"
fi

lpadmin -p "${PRINTER_NAME}" -E -v "${USB_URI}" -m "${MODEL}" || true
lpadmin -p "${PRINTER_NAME}" -o printer-is-shared=true || true
lpadmin -p "${PRINTER_NAME}" -o document-format-default=application/octet-stream || true
cupsenable "${PRINTER_NAME}" || true
accept "${PRINTER_NAME}" || true

echo "== RAW Port 9100 per socat (OrderAssist) =="
cat > /etc/systemd/system/socket-9100.service <<EOF
[Unit]
Description=RAW TCP 9100 -> ${USB_DEVICE} (ESC/POS)
After=network.target

[Service]
ExecStart=/usr/bin/socat -u TCP-LISTEN:9100,fork,reuseaddr FILE:${USB_DEVICE},nonblock,cloexec
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now socket-9100.service

get_ips() {
  ip -4 addr show scope global | awk '/inet /{print $2}' | cut -d/ -f1 | paste -sd ", " -
}
PI_IPS="$(get_ips)"
HOSTNAME="$(hostname)"

echo
echo "=============================================="
echo "✅ Installation abgeschlossen"
echo "=============================================="
echo "Hostname:         ${HOSTNAME}"
echo "IP(s):            ${PI_IPS}"
echo "CUPS Web UI:      http://${PI_IPS%%,*}:631"
echo "Druckername:      ${PRINTER_NAME}"
echo
echo "OrderAssist (RAW):"
echo "  IP:             ${PI_IPS%%,*}"
echo "  Port:           9100"
echo "  Typ:            RAW / Socket / ESC-POS"
echo "  Hinweis:         KEIN http:// und KEIN /printers/... in der App"
echo
echo "== Checkliste =="
echo "1) Ports offen?"
netstat -tlnp | egrep ':(631|9100)\s' || echo "   ❌ Ports 631/9100 nicht sichtbar"

echo
echo "2) USB-Device vorhanden?"
ls -l "${USB_DEVICE}" || true

echo
echo "3) Testdruck RAW (lokal) – optional:"
echo "   echo -e \"TEST\\n\\n\\n\" | nc 127.0.0.1 9100"

echo
echo "4) Testdruck CUPS (lokal) – optional:"
echo "   echo \"Test über CUPS\" | lp -d ${PRINTER_NAME}"
echo "=============================================="
