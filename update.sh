#!/usr/bin/env bash
#
# Compatibility shim.
#
# The old project used "git pull && bash update.sh" to rebuild the CUPS filter
# and restart socat.  BonBridge updates by simply running the installer again:
# it stops the service, replaces /opt/bonbridge, keeps /etc/bonbridge/config.yaml
# and starts the service back up.
#
# This file exists so that anyone following the old instructions still ends up
# with a working system.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"

echo "==> BonBridge update"
echo "    (update.sh is deprecated - install.sh is now also the updater)"
echo

if [ "$(id -u)" -ne 0 ]; then
  echo "please run as root:  sudo bash update.sh" >&2
  exit 1
fi

if [ -d "$SCRIPT_DIR/.git" ]; then
  echo "==> git pull"
  git -C "$SCRIPT_DIR" pull --ff-only || echo "    (git pull failed, continuing with the local files)"
fi

exec bash "$SCRIPT_DIR/install.sh" "$@"
