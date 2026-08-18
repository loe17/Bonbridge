#!/usr/bin/env bash
#
# BonBridge one-command installer
#
#   curl -fsSL https://raw.githubusercontent.com/loe17/bonbridge/main/install.sh | sudo bash
#
# or, from a checkout:
#
#   sudo bash install.sh
#
# Options (environment variables or flags):
#   --with-cups        also install CUPS and the vendored zj-58 filter
#   --branch NAME      install from this git branch instead of the default
#   --no-start         install but do not start the service
#   --web-port N       web interface port (default 8080)
#   --raw-port N       RAW listening port (default 9100 - OrderAssist needs 9100)
#
# Supported: Debian 11/12/13, Raspberry Pi OS (32/64 bit), Ubuntu 22.04+
# Architectures: x86_64, aarch64, armv7l, armv6l
#
set -euo pipefail

REPO_OWNER="${BONBRIDGE_REPO_OWNER:-loe17}"
REPO_NAME="${BONBRIDGE_REPO_NAME:-bonbridge}"
BRANCH="${BONBRIDGE_BRANCH:-main}"
INSTALL_DIR="${BONBRIDGE_INSTALL_DIR:-/opt/bonbridge}"
CONFIG_DIR="${BONBRIDGE_CONFIG_DIR:-/etc/bonbridge}"
STATE_DIR="${BONBRIDGE_STATE_DIR:-/var/lib/bonbridge}"
LOG_DIR="${BONBRIDGE_LOG_DIR:-/var/log/bonbridge}"
WITH_CUPS=0
DO_START=1
WEB_PORT=8080
RAW_PORT=9100

C_OK=$'\033[0;32m'; C_WARN=$'\033[0;33m'; C_ERR=$'\033[0;31m'; C_B=$'\033[1m'; C_0=$'\033[0m'
if [ ! -t 1 ]; then C_OK=""; C_WARN=""; C_ERR=""; C_B=""; C_0=""; fi

info()  { printf '%s==>%s %s\n' "$C_B" "$C_0" "$*"; }
ok()    { printf '%s  ok%s %s\n' "$C_OK" "$C_0" "$*"; }
warn()  { printf '%s  !!%s %s\n' "$C_WARN" "$C_0" "$*"; }
die()   { printf '%s ERR%s %s\n' "$C_ERR" "$C_0" "$*" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case "$1" in
    --with-cups) WITH_CUPS=1 ;;
    --no-start)  DO_START=0 ;;
    --branch)    BRANCH="${2:?--branch needs a value}"; shift ;;
    --web-port)  WEB_PORT="${2:?--web-port needs a value}"; shift ;;
    --raw-port)  RAW_PORT="${2:?--raw-port needs a value}"; shift ;;
    -h|--help)   sed -n '2,20p' "$0"; exit 0 ;;
    *) die "unknown option: $1" ;;
  esac
  shift
done

[ "$(id -u)" -eq 0 ] || die "please run as root:  sudo bash install.sh"

# ---------------------------------------------------------------------------
# 1. Platform checks
# ---------------------------------------------------------------------------
info "Checking the system"
ARCH="$(uname -m)"
case "$ARCH" in
  x86_64|amd64|aarch64|arm64|armv7l|armv6l) ok "architecture: $ARCH" ;;
  *) warn "untested architecture: $ARCH - continuing anyway" ;;
esac

if [ -r /etc/os-release ]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  ok "system: ${PRETTY_NAME:-$NAME}"
else
  warn "/etc/os-release not found"
fi

command -v systemctl >/dev/null 2>&1 || die "systemd is required"
command -v apt-get   >/dev/null 2>&1 || die "this installer supports Debian based systems (apt)"

MODEL=""
[ -r /proc/device-tree/model ] && MODEL="$(tr -d '\0' < /proc/device-tree/model)"
[ -n "$MODEL" ] && ok "board: $MODEL"

# ---------------------------------------------------------------------------
# 2. Packages
# ---------------------------------------------------------------------------
info "Installing packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
PACKAGES="python3 python3-yaml python3-usb python3-serial libusb-1.0-0 iproute2 ca-certificates"
# avahi makes bonbridge.local work; harmless if it is already there
PACKAGES="$PACKAGES avahi-daemon"
if [ "$WITH_CUPS" -eq 1 ]; then
  PACKAGES="$PACKAGES cups cups-filters build-essential cmake libcups2-dev libcupsimage2-dev"
fi
# shellcheck disable=SC2086
apt-get install -y -qq $PACKAGES || die "package installation failed"
ok "packages installed"

# ---------------------------------------------------------------------------
# 3. Source: local checkout or download
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || echo "")"
SOURCE_DIR=""
if [ -n "$SCRIPT_DIR" ] && [ -d "$SCRIPT_DIR/src/bonbridge" ]; then
  SOURCE_DIR="$SCRIPT_DIR"
  info "Installing from local checkout: $SOURCE_DIR"
else
  info "Downloading BonBridge ($REPO_OWNER/$REPO_NAME, branch $BRANCH)"
  command -v curl >/dev/null 2>&1 || apt-get install -y -qq curl
  command -v tar  >/dev/null 2>&1 || apt-get install -y -qq tar
  TMPDIR_DL="$(mktemp -d)"
  trap 'rm -rf "$TMPDIR_DL"' EXIT
  URL="https://codeload.github.com/${REPO_OWNER}/${REPO_NAME}/tar.gz/refs/heads/${BRANCH}"
  curl -fsSL "$URL" -o "$TMPDIR_DL/bonbridge.tar.gz" \
    || die "download failed: $URL"
  tar -xzf "$TMPDIR_DL/bonbridge.tar.gz" -C "$TMPDIR_DL"
  SOURCE_DIR="$(find "$TMPDIR_DL" -maxdepth 1 -type d -name "${REPO_NAME}-*" | head -n1)"
  [ -d "${SOURCE_DIR:-}/src/bonbridge" ] || die "downloaded archive looks wrong"
  ok "downloaded"
fi

# ---------------------------------------------------------------------------
# 4. Stop a running instance, then copy the files
# ---------------------------------------------------------------------------
if systemctl is-active --quiet bonbridge 2>/dev/null; then
  info "Stopping the running service"
  systemctl stop bonbridge || true
fi

info "Installing to $INSTALL_DIR"
mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$STATE_DIR/spool" "$LOG_DIR"
rm -rf "$INSTALL_DIR/src" "$INSTALL_DIR/vendor" "$INSTALL_DIR/docs" "$INSTALL_DIR/packaging"
cp -a "$SOURCE_DIR/src"       "$INSTALL_DIR/"
cp -a "$SOURCE_DIR/vendor"    "$INSTALL_DIR/"
cp -a "$SOURCE_DIR/docs"      "$INSTALL_DIR/" 2>/dev/null || true
cp -a "$SOURCE_DIR/packaging" "$INSTALL_DIR/"
for file in VERSION LICENSE NOTICE README.md README.de.md CHANGELOG.md uninstall.sh install.sh; do
  [ -f "$SOURCE_DIR/$file" ] && cp -a "$SOURCE_DIR/$file" "$INSTALL_DIR/"
done
chmod +x "$INSTALL_DIR/uninstall.sh" 2>/dev/null || true
ok "files installed ($(cat "$INSTALL_DIR/VERSION" 2>/dev/null || echo unknown))"

# Convenience wrapper so "bonbridge scan" works from any shell.
cat > /usr/local/bin/bonbridge <<EOF
#!/usr/bin/env bash
# BonBridge command line wrapper (generated by install.sh)
export PYTHONPATH="${INSTALL_DIR}/src\${PYTHONPATH:+:\$PYTHONPATH}"
export BONBRIDGE_ROOT="${INSTALL_DIR}"
exec python3 -m bonbridge "\$@"
EOF
chmod 0755 /usr/local/bin/bonbridge
ok "command line tool: bonbridge"

# ---------------------------------------------------------------------------
# 5. Configuration
# ---------------------------------------------------------------------------
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
  info "Creating $CONFIG_DIR/config.yaml"
  cat > "$CONFIG_DIR/config.yaml" <<EOF
# BonBridge configuration
# Docs: $INSTALL_DIR/docs/de/  (deutsch)  |  $INSTALL_DIR/docs/en/  (english)
# After editing:  sudo systemctl restart bonbridge
version: 1
hostname_label: ""
web:
  bind: 0.0.0.0
  port: ${WEB_PORT}
  language: de
raw:
  # OrderAssist and most POS apps always use 9100 and cannot change it.
  port: ${RAW_PORT}
  max_connections: 8
discovery:
  mdns: true
  enpc: false
logging:
  level: INFO
# Printers are created automatically on first start.
# For several print groups give every printer its own IP address in "bind"
# and create the IP alias with:  systemctl enable --now bonbridge-ip@eth0:192.168.1.51/24
printers: []
EOF
  ok "configuration created"
else
  ok "keeping existing $CONFIG_DIR/config.yaml"
fi

# ---------------------------------------------------------------------------
# 6. systemd
# ---------------------------------------------------------------------------
info "Installing the systemd service"
install -m 0644 "$INSTALL_DIR/packaging/systemd/bonbridge.service"    /etc/systemd/system/bonbridge.service
install -m 0644 "$INSTALL_DIR/packaging/systemd/bonbridge-ip@.service" /etc/systemd/system/bonbridge-ip@.service
systemctl daemon-reload
systemctl enable bonbridge >/dev/null 2>&1 || true
ok "service installed"

# udev rule so a replugged printer is picked up without a restart
install -m 0644 "$INSTALL_DIR/packaging/udev/99-bonbridge.rules" /etc/udev/rules.d/99-bonbridge.rules 2>/dev/null || true
udevadm control --reload-rules 2>/dev/null || true

# ---------------------------------------------------------------------------
# 7. Optional CUPS module
# ---------------------------------------------------------------------------
if [ "$WITH_CUPS" -eq 1 ]; then
  info "Building the vendored zj-58 CUPS filter"
  BUILD_DIR="$INSTALL_DIR/vendor/zj-58/build"
  rm -rf "$BUILD_DIR"; mkdir -p "$BUILD_DIR"
  ( cd "$BUILD_DIR" && cmake .. >/dev/null && make -j"$(nproc)" >/dev/null && make install >/dev/null ) \
    && ok "zj-58 filter installed" || warn "zj-58 build failed - CUPS printing will be unavailable"
  systemctl restart cups || true
  info "Registering the CUPS queue via BonBridge"
  bash "$INSTALL_DIR/packaging/cups/setup-cups.sh" || warn "CUPS queue setup failed - see docs"
fi

# ---------------------------------------------------------------------------
# 8. Start
# ---------------------------------------------------------------------------
if [ "$DO_START" -eq 1 ]; then
  info "Starting BonBridge"
  systemctl restart bonbridge
  sleep 2
  if systemctl is-active --quiet bonbridge; then
    ok "service is running"
  else
    warn "service did not start - check: journalctl -u bonbridge -n 50"
  fi
fi

# ---------------------------------------------------------------------------
# 9. Summary
# ---------------------------------------------------------------------------
IP="$(ip -4 -o addr show scope global 2>/dev/null | awk '{print $4}' | cut -d/ -f1 | head -n1)"
IP="${IP:-127.0.0.1}"
HOST="$(hostname)"

echo
printf '%s================================================================%s\n' "$C_B" "$C_0"
printf '%s BonBridge installed%s\n' "$C_OK" "$C_0"
printf '%s================================================================%s\n' "$C_B" "$C_0"
echo
echo "  Web interface :  http://${IP}:${WEB_PORT}/    (also http://${HOST}.local:${WEB_PORT}/)"
echo "  POS printing  :  ${IP}   port ${RAW_PORT}   (RAW / ESC-POS)"
echo
echo "  In OrderAssist: Drucker -> + Hinzufuegen -> IP address ${IP}"
echo "  The port is fixed at 9100 in the app and does not need to be entered."
echo
echo "  Status        :  systemctl status bonbridge"
echo "  Log           :  journalctl -u bonbridge -f"
echo "  Detect devices:  bonbridge scan"
echo "  Support report:  bonbridge report > report.txt"
echo "  Uninstall     :  sudo bash ${INSTALL_DIR}/uninstall.sh"
echo
if ! ls /dev/usb/lp* >/dev/null 2>&1 && ! lsusb 2>/dev/null | grep -qiE 'epson|printer|star micronics'; then
  warn "No printer detected yet."
  echo "        - the printer needs its OWN 24 V power supply, USB alone is not enough"
  echo "        - Raspberry Pi Zero: use the inner Micro-USB socket (marked USB, not PWR IN)"
  echo "        - Raspberry Pi 4: prefer the black USB 2.0 ports"
  echo "        - check with:  lsusb   and   dmesg | tail -n 20"
fi
echo
