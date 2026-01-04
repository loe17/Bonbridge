#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKDIR="/opt/rpi-escpos-printserver"
ZJ_DIR="${WORKDIR}/zj-58"

echo "== Update: Repo + zj-58 + Services =="

cd "${REPO_DIR}"
echo "== git pull =="
git pull --ff-only

echo "== apt update (keine Upgrades) =="
sudo apt update

echo "== Update & Rebuild zj-58 =="
sudo mkdir -p "${WORKDIR}"
if [[ ! -d "${ZJ_DIR}" ]]; then
  sudo git clone https://github.com/klirichek/zj-58.git "${ZJ_DIR}"
else
  sudo git -C "${ZJ_DIR}" pull --ff-only
fi

sudo mkdir -p "${ZJ_DIR}/build"
cd "${ZJ_DIR}/build"
sudo cmake ..
sudo make -j"$(nproc)"
sudo make install

echo "== Restart services =="
sudo systemctl restart cups || true
sudo systemctl restart socket-9100 || true

echo "== Status =="
sudo netstat -tlnp | egrep ':(631|9100)\s' || true
echo "Done."
