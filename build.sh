#!/bin/bash
set -euo pipefail

series=${1:-main}
sdk=${2:-}
version=${3:-}

manifest="build/$series.yaml"
report="build/$series.json"

generate=(--series "$series" --out "$manifest" --report "$report")
if [[ -n $sdk ]]; then
  generate+=(--sdk "$sdk")
fi
if [[ -n $version ]]; then
  generate+=(--version "$version")
fi
python3 scripts/gen-manifest.py "${generate[@]}"

flatpak-builder --user --force-clean --install-deps-from=flathub \
  --repo=build/repo "build/$series.build" "$manifest"

read -r id sdk < <(python3 -c "import json; info = json.load(open('$report')); print(info['id'], info['sdk'])")
runtime=(--runtime-repo=https://dl.flathub.org/repo/flathub.flatpakrepo --runtime "$sdk")
mkdir -p build/bundles
flatpak build-bundle build/repo "build/bundles/$id-$sdk.flatpak" "$id" "${runtime[@]}"
flatpak build-bundle build/repo "build/bundles/$id.Debug-$sdk.flatpak" "$id.Debug" "${runtime[@]}"

echo "bundles written to build/bundles/"
