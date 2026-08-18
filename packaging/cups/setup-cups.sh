#!/usr/bin/env bash
#
# Optional: register a CUPS queue that prints *through* BonBridge.
#
# Important design decision: the queue does NOT talk to /dev/usb/lp0.  It
# sends to socket://127.0.0.1:9100, i.e. into BonBridge's own RAW listener.
# That keeps a single owner for the printer device and makes it impossible
# for CUPS and the POS application to interleave their output - which is
# exactly what went wrong in the old CUPS + socat setup.
#
# The rasterising filter used here is zj-58 by Aleksey N. Vinogradov
# (BSD 2-Clause), vendored at vendor/zj-58/ -> https://github.com/klirichek/zj-58
# See docs/en/09-references.md for the full list of third-party code.
#
# Usage:  sudo bash setup-cups.sh [queue-name] [raw-port]
#
set -euo pipefail

QUEUE="${1:-BonBridge}"
PORT="${2:-9100}"

[ "$(id -u)" -eq 0 ] || { echo "run as root" >&2; exit 1; }
command -v lpadmin >/dev/null 2>&1 || { echo "CUPS is not installed" >&2; exit 1; }

echo "==> Creating CUPS queue '$QUEUE' -> socket://127.0.0.1:$PORT"

# Prefer the vendored zj-58 PPD (works for most ESC/POS printers); fall back
# to a driverless raw queue when the filter is not installed.
MODEL=""
if lpinfo -m 2>/dev/null | grep -qi 'zj-80'; then
  MODEL="$(lpinfo -m 2>/dev/null | awk 'tolower($0) ~ /zj-80/ {print $1; exit}')"
  echo "    driver: $MODEL (vendored zj-58 filter)"
elif lpinfo -m 2>/dev/null | grep -qiE '(^| )raw( |$)'; then
  MODEL="raw"
  echo "    driver: raw"
fi

if [ -n "$MODEL" ]; then
  lpadmin -p "$QUEUE" -E -v "socket://127.0.0.1:${PORT}" -m "$MODEL"
else
  # Newer CUPS releases dropped the built-in "raw" model.  A queue without a
  # driver behaves the same way for RAW data.
  echo "    driver: none (RAW passthrough)"
  lpadmin -p "$QUEUE" -E -v "socket://127.0.0.1:${PORT}"
fi

lpadmin -p "$QUEUE" -o printer-is-shared=true
lpadmin -p "$QUEUE" -o document-format-default=application/octet-stream
cupsenable "$QUEUE" || true
if command -v cupsaccept >/dev/null 2>&1; then
  cupsaccept "$QUEUE" || true
else
  /usr/sbin/accept "$QUEUE" 2>/dev/null || true
fi

echo "==> done"
echo "    Test:  echo 'Hello' | lp -d $QUEUE"
echo "    CUPS web interface: http://$(hostname -I 2>/dev/null | awk '{print $1}'):631/"
echo
echo "    NOTE: CUPS is optional and is NOT needed for OrderAssist."
echo "          OrderAssist prints directly to port ${PORT}."
