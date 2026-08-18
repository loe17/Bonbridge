#!/usr/bin/env bash
#
# Remove BonBridge.  Configuration and spool data are kept unless --purge is
# given, so a reinstall keeps your printers.
#
#   sudo bash uninstall.sh
#   sudo bash uninstall.sh --purge
#
set -euo pipefail

INSTALL_DIR="${BONBRIDGE_INSTALL_DIR:-/opt/bonbridge}"
CONFIG_DIR="${BONBRIDGE_CONFIG_DIR:-/etc/bonbridge}"
STATE_DIR="${BONBRIDGE_STATE_DIR:-/var/lib/bonbridge}"
LOG_DIR="${BONBRIDGE_LOG_DIR:-/var/log/bonbridge}"
PURGE=0

[ "${1:-}" = "--purge" ] && PURGE=1
[ "$(id -u)" -eq 0 ] || { echo "please run as root: sudo bash uninstall.sh" >&2; exit 1; }

echo "==> Stopping services"
systemctl disable --now bonbridge 2>/dev/null || true
for unit in $(systemctl list-units --all --plain --no-legend 'bonbridge-ip@*' 2>/dev/null | awk '{print $1}'); do
  systemctl disable --now "$unit" 2>/dev/null || true
done

echo "==> Removing unit files"
rm -f /etc/systemd/system/bonbridge.service /etc/systemd/system/bonbridge-ip@.service
systemctl daemon-reload

echo "==> Removing program files"
rm -rf "$INSTALL_DIR"
rm -f /usr/local/bin/bonbridge
rm -f /etc/udev/rules.d/99-bonbridge.rules
rm -f /etc/avahi/services/bonbridge.service
udevadm control --reload-rules 2>/dev/null || true
systemctl reload avahi-daemon 2>/dev/null || true

if [ "$PURGE" -eq 1 ]; then
  echo "==> Purging configuration and data"
  rm -rf "$CONFIG_DIR" "$STATE_DIR" "$LOG_DIR"
else
  echo "==> Keeping $CONFIG_DIR, $STATE_DIR and $LOG_DIR (use --purge to remove them)"
fi

echo
echo "BonBridge removed."
echo "Note: CUPS, avahi-daemon and the Python packages were left installed."
echo "If a CUPS queue was created, remove it with:  sudo lpadmin -x BonBridge"
