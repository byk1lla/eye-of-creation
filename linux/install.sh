#!/usr/bin/env bash
# Linux: Eye of Creation'ı XScreenSaver'a ekler (video mpv ile oynatılır).
#
# Gerekenler: xscreensaver + mpv
#   Debian/Ubuntu: sudo apt install xscreensaver mpv
#   Fedora:        sudo dnf install xscreensaver mpv
#   Arch:          sudo pacman -S xscreensaver mpv
set -euo pipefail
cd "$(dirname "$0")"

for cmd in mpv xscreensaver; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "[!] '$cmd' bulunamadı / not found. Kur / install it first (see the top of this script)."
    exit 1
  fi
done

VIDEO_SRC="../assets/EyeOfCreation.mp4"
[ -f "$VIDEO_SRC" ] || { echo "[!] $VIDEO_SRC yok / missing"; exit 1; }

DEST="${XDG_DATA_HOME:-$HOME/.local/share}/eye-of-creation"
mkdir -p "$DEST"
cp "$VIDEO_SRC" "$DEST/EyeOfCreation.mp4"

HACK="$DEST/eye-of-creation-hack"
cat > "$HACK" <<EOF
#!/bin/sh
# XScreenSaver hack: videoyu XScreenSaver'ın penceresinde döngüyle oynatır.
WID="\${XSCREENSAVER_WINDOW:-}"
if [ -n "\$WID" ]; then
  exec mpv --really-quiet --no-audio --loop=inf --no-osc --no-input-default-bindings \\
    --panscan=1.0 --hwdec=auto --wid="\$WID" "$DEST/EyeOfCreation.mp4"
else
  exec mpv --really-quiet --no-audio --loop=inf --no-osc --fs \\
    --panscan=1.0 --hwdec=auto "$DEST/EyeOfCreation.mp4"
fi
EOF
chmod +x "$HACK"

CONF="$HOME/.xscreensaver"
if [ ! -f "$CONF" ]; then
  echo "[i] ~/.xscreensaver yok, oluşturuluyor / creating it..."
  # xscreensaver-settings (ya da eski sürümlerde xscreensaver-demo) ilk açılışta varsayılan dosyayı yazar
  (xscreensaver-settings >/dev/null 2>&1 || xscreensaver-demo >/dev/null 2>&1) &
  sleep 3
  pkill -f "xscreensaver-(settings|demo)" 2>/dev/null || true
fi
[ -f "$CONF" ] || { echo "[!] ~/.xscreensaver oluşturulamadı. Bir kez 'xscreensaver-settings' aç, sonra bu scripti tekrar çalıştır."; exit 1; }

if grep -q "eye-of-creation-hack" "$CONF"; then
  echo "[i] Zaten ekli / already registered."
else
  cp "$CONF" "$CONF.bak-eye-of-creation"
  # 'programs:' satırının hemen altına ekle
  awk -v line="  \"Eye of Creation\"  $HACK \\\\n\\\\" '
    { print }
    /^programs:/ && !done { print line; done=1 }
  ' "$CONF.bak-eye-of-creation" > "$CONF"
  echo "[i] ~/.xscreensaver güncellendi (yedek: ~/.xscreensaver.bak-eye-of-creation)"
fi

# XScreenSaver çalışıyorsa yeni ayarı okusun
xscreensaver-command -restart >/dev/null 2>&1 || true

echo
echo "Tamam / Done."
echo "  - Ayarlar / settings:  xscreensaver-settings  →  listeden 'Eye of Creation'ı seç / pick it from the list"
echo "  - Hemen dene / try now:  $HACK"
