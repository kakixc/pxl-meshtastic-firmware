# PXL Meshtastic Firmware

Unofficial Meshtastic firmware builds with a small set of PXL UI improvements.

PXL firmware stays compatible with the normal Meshtastic mesh and does not modify the LoRa protocol, routing behavior, regional limits, or radio power limits.

> Current PXL revision: **PXL 0.2**

Development of PXL 0.3 for Heltec V3 is on the
`feature/pxl-0.3-low-power` branch. Its manual GitHub Actions workflow builds
an artifact from the official Meshtastic `v2.7.26.54e0d8d` tag. This is a
development build; power consumption and button wake behavior require tests
on a physical Heltec V3 before release.

The feature-branch workflow defaults to a PXL 0.2 image with a PM-capable
Arduino framework and **without Dynamic Light Sleep**. A manual
`experimental_dynamic_sleep` input builds a separately named PXL 0.3
experimental artifact with the RTC wake prototype. This option does not
publish a release and has only passed compilation. The branch also contains
Heltec V3-only candidates to advance the OLED frame
on a short USER press that wakes an off screen and to poll USER promptly after
ordinary Light Sleep; hardware validation is pending.
PXL 0.3 runtime power saving remains under investigation. See
[`docs/pxl-0.3-validation.md`](docs/pxl-0.3-validation.md) for known wake and
radio risks and the required device tests.

To request the experimental image manually from this branch:

```text
gh workflow run build.yml --ref feature/pxl-0.3-low-power -f experimental_dynamic_sleep=true
```

The resulting `PXL.3-experimental-update.bin` is a normal application image,
separate from the factory image. Configuration retention still needs a real
update test on Heltec V3; no final PXL 0.3 release is published automatically.

## PXL changes

### PXL boot

A lightweight OEM-style boot stage:

```text
        PXL
       MESH

   [██████░░░░]

             PXL 0.2
```

On normal OLED/TFT devices the progress bar is animated.

E-Ink targets use a static version to avoid unnecessary display refreshes.

### PXL STATUS

Adds a separate status screen with live device information:

```text
      PXL STATUS

BAT 82%  4.01V
NODES 200/240
CH 2.4%  TX 0.1%
ROLE MUTE
```

Values are read from the running Meshtastic firmware.

### Cyrillic OLED support

`OLED_RU` is enabled so Russian/Cyrillic text can be displayed correctly on supported screens.

This does **not** translate the Meshtastic UI.

The normal interface remains unchanged.

### Shorter boot

The stock boot stage is shortened before switching to the PXL boot screen.

---

## What is not changed

PXL builds intentionally leave the radio stack alone.

The following stay upstream Meshtastic behavior:

- LoRa protocol
- routing
- packet format
- encryption
- channels
- region configuration
- RU regional limits
- TX power limits
- Bluetooth protocol
- Meshtastic app compatibility
- node database format
- configuration format

There is no custom high-power patch.

---

## Supported builds

| Device | PlatformIO target | Output |
|---|---|---|
| Heltec V3 | `heltec-v3` | BIN |
| Heltec V4 | `heltec-v4` | BIN |
| LilyGo T3S3 | `tlora-t3s3-v1` | BIN |
| LilyGo T3S3 E-Paper | `tlora-t3s3-epaper` | BIN |
| LilyGo T3S3 E-Paper InkHUD | `tlora-t3s3-epaper-inkhud` | BIN |
| Heltec Mesh Node T114 | `heltec-mesh-node-t114` | UF2 |
| Heltec Mesh Node T096 | `heltec-mesh-node-t096` | UF2 |

Not every PXL UI feature has been physically tested on every target.

The primary test device is currently **Heltec V3**.

---

## Release files

ESP32 builds normally contain two images.

### Update

```text
...-update.bin
```

Use this for normal upgrades.

It replaces the firmware application without intentionally erasing the device configuration/data partitions.

This is the recommended file for an already configured node.

### Factory

```text
...-factory.bin
```

Use this for a clean installation.

A factory installation may erase existing settings depending on the flashing method.

Do not use it for a normal update unless you specifically want a clean installation.

### nRF52840

nRF52840 targets use `.uf2`.

The workflow publishes a normal update UF2 and also publishes a factory UF2 when the upstream target actually produces one.

---

## Updating an ESP32 node

For an existing configured node:

1. Back up anything important.
2. Open the official Meshtastic Web Flasher.
3. Select the correct device.
4. Load the PXL `-update.bin`.
5. Use **Update**.
6. Do not select Full Erase / Clean Install.

After reboot, existing Meshtastic configuration should normally remain intact.

For experimental builds, keeping a backup before flashing is still recommended.

---

## Versioning

PXL releases are based on an exact official Meshtastic release.

Example:

```text
v2.7.26.54e0d8d-PXL.2
```

Where:

```text
v2.7.26.54e0d8d = upstream Meshtastic release
PXL.2              = PXL firmware revision
```

The boot screen additionally shows the human-readable PXL version:

```text
PXL 0.2
```

---

## Automatic builds

GitHub Actions checks the latest official stable Meshtastic release every day.

For a new upstream release, the workflow:

1. resolves the official Meshtastic stable tag;
2. clones that exact tag;
3. initializes upstream submodules;
4. applies the PXL modifications;
5. validates the generated diff;
6. builds all supported targets independently;
7. packages update/factory firmware where available;
8. creates SHA-256 checksums;
9. publishes one GitHub Release containing all successful board builds.

The build can also be started manually and pointed at a specific Meshtastic tag.

The patcher intentionally fails if important upstream source layout changes instead of silently patching an unexpected location.

---

## Build philosophy

PXL Meshtastic is intentionally a small patch set.

The goal is:

```text
Meshtastic
    +
Cyrillic display support
    +
clean PXL boot
    +
useful local status UI
```

Not:

```text
custom radio protocol
custom regional limits
maximum-power hacks
incompatible mesh fork
```

PXL nodes should continue communicating normally with standard Meshtastic nodes.

---

## Security

Do not commit raw device flash backups.

A full flash dump can contain:

- Meshtastic configuration
- channel information
- keys
- node database
- persistent application data

Keep dumps outside the repository.

Also never publish private channel PSKs.

---

## Status

### PXL 0.1

First physical Heltec V3 test.

Validated:

- update without full erase
- configuration preserved
- NodeDB preserved
- LoRa startup
- Bluetooth startup
- `OLED_RU`
- first `PXL STATUS` implementation

### PXL 0.2

Current revision.

Changes:

- fixed PXL STATUS spacing
- cleaner compact role display
- `AIR` renamed to `TX`
- animated PXL MESH boot
- PXL 0.2 boot branding
- multi-board CI
- update + factory release packaging

---

## Upstream

PXL Meshtastic is based on the open-source Meshtastic firmware project.

This repository is an unofficial community project and is not an official Meshtastic release.
