# intel-compute-runtime-flatpak

Unofficial flatpak extensions that provide the Intel OpenCL and Level Zero drivers to the freedesktop runtime. 

| extension | hardware | upstream series |
|---|---|---|
| `org.freedesktop.Platform.GL.OpenCLIntel` | Gen12 and newer | the latest release |
| `org.freedesktop.Platform.GL.OpenCLIntelLegacy` | Gen8, Gen9, Gen11 | the 24.35 legacy branch |

Bundles are built for the current freedesktop SDK branches and published on the [releases page](../../releases).  
Each release includes the driver itself, the debugging symbols and some other metadata.

## Installing

```sh
flatpak install --user ./org.freedesktop.Platform.GL.OpenCLIntel-<Freedesktop SDK version>.flatpak
```

Running an application with the driver:

```sh
FLATPAK_GL_DRIVERS=OpenCLIntel:default flatpak run org.freedesktop.Platform.ClInfo
```

If you use systemd, you can use the following to set this permanently into your environment:

```sh
mkdir -p ~/.config/environment.d
echo FLATPAK_GL_DRIVERS=OpenCLIntel:default | tee ~/.config/environment.d/60-flatpak_gl_drivers.conf
```

### Using both drivers

Both extensions can be installed and used at the same time:

```sh
FLATPAK_GL_DRIVERS=OpenCLIntel:OpenCLIntelLegacy:default flatpak run org.freedesktop.Platform.ClInfo
```

