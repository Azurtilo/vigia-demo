#!/bin/sh
# Build and preserve the downloadable APK outside Flutter's temporary outputs.
# Runs on macOS and on Windows with Git Bash. Flutter: VIGIA_FLUTTER_BIN, then
# .tooling/flutter, then the one on PATH. Server: VIGIA_API_URL.
set -eu
vigia_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
if [ -n "${VIGIA_FLUTTER_BIN:-}" ]; then
  vigia_flutter=$VIGIA_FLUTTER_BIN
elif [ -x "$vigia_root/.tooling/flutter/bin/flutter" ]; then
  vigia_flutter=$vigia_root/.tooling/flutter/bin/flutter
else
  vigia_flutter=flutter
fi
cd "$vigia_root/mobile"
"$vigia_flutter" build apk --debug --target-platform android-arm64 --dart-define="API_URL=${VIGIA_API_URL:-http://10.0.2.2:8000}"
mkdir -p "$vigia_root/artifacts/android"
cp build/app/outputs/flutter-apk/app-debug.apk "$vigia_root/artifacts/android/VIGIA-android-prueba.apk.tmp"
mv "$vigia_root/artifacts/android/VIGIA-android-prueba.apk.tmp" "$vigia_root/artifacts/android/VIGIA-android-prueba.apk"
printf '%s\n' "APK disponible en artifacts/android/VIGIA-android-prueba.apk"
