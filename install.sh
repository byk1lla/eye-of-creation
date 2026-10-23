#!/usr/bin/env bash
# Ekran koruyucuyu derleyip ~/Library/Screen Savers içine kurar.
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v swiftc >/dev/null 2>&1; then
  echo "swiftc bulunamadı. Önce şunu çalıştır: xcode-select --install"
  exit 1
fi

./screensaver/build.sh

DEST="$HOME/Library/Screen Savers"
mkdir -p "$DEST"
rm -rf "$DEST/EyeOfCreation.saver"
cp -R screensaver/build/EyeOfCreation.saver "$DEST/"
xattr -dr com.apple.quarantine "$DEST/EyeOfCreation.saver" 2>/dev/null || true

# Eski sürüm hafızada kalmasın
killall legacyScreenSaver 2>/dev/null || true

echo "Kuruldu: $DEST/EyeOfCreation.saver"
echo "Sistem Ayarları > Ekran Koruyucu açılıyor, listeden 'Eye of Creation'ı seç."
open "x-apple.systempreferences:com.apple.ScreenSaver-Settings.extension" 2>/dev/null || true
