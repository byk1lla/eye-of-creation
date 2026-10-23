#!/usr/bin/env bash
# EyeOfCreation.saver paketini derler (Xcode Command Line Tools yeterli).
set -euo pipefail
cd "$(dirname "$0")"

OUT="build/EyeOfCreation.saver"
rm -rf build
mkdir -p "$OUT/Contents/MacOS" "$OUT/Contents/Resources"

for arch in arm64 x86_64; do
  swiftc -O \
    -module-name EyeOfCreation \
    -parse-as-library \
    -emit-library \
    -target "$arch-apple-macos12.0" \
    -framework ScreenSaver -framework AVFoundation -framework AppKit \
    Sources/EyeOfCreationView.swift \
    -o "build/EyeOfCreation-$arch"
done

lipo -create build/EyeOfCreation-arm64 build/EyeOfCreation-x86_64 \
  -output "$OUT/Contents/MacOS/EyeOfCreation"

cp Info.plist "$OUT/Contents/"
cp ../assets/EyeOfCreation.mp4 thumbnail.png thumbnail@2x.png "$OUT/Contents/Resources/"

codesign --force --deep --sign - "$OUT"
echo "Hazır: $(pwd)/$OUT"
