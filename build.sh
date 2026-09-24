#!/bin/bash
rm -r build/
mkdir build/
cd build/ || exit 1
mkdir bundles/

VERSION=26.08

flatpak-builder --repo=build --install-deps-from=flathub --user --force-clean build --install ../org.freedesktop.Platform.GL.OpenCLIntel.yaml || exit 1
echo generating normal bundle
flatpak build-bundle repo bundles/org.freedesktop.Platform.GL.OpenCLIntel.flatpak org.freedesktop.Platform.GL.OpenCLIntel --runtime-repo=https://dl.flathub.org/repo/flathub.flatpakrepo --runtime "$VERSION" || exit 1
echo generating debug bundle
flatpak build-bundle repo bundles/org.freedesktop.Platform.GL.OpenCLIntel.Debug.flatpak org.freedesktop.Platform.GL.OpenCLIntel.Debug --runtime-repo=https://dl.flathub.org/repo/flathub.flatpakrepo --runtime "$VERSION" || exit 1
