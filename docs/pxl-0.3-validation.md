# PXL 0.3 Heltec V3 validation

PXL 0.3 is an experimental Heltec V3 project based on official Meshtastic
`v2.7.26.54e0d8d`. A complete PXL 0.3 image is not ready. This document
separates build evidence from device behavior. No Heltec V3 or current meter
was available for this validation.

## Software evidence

| Check | Result |
| --- | --- |
| Official tag and retained PXL 0.2 display patch | Local build and manual Actions baseline passed |
| PM-capable Arduino 2.x framework, ESP32-S3 | `CONFIG_PM_ENABLE=y` and `CONFIG_FREERTOS_USE_TICKLESS_IDLE=y` verified; local build and [manual Actions run](https://github.com/kakixc/pxl-meshtastic-firmware/actions/runs/38999865180) passed |
| Full PXL 0.3 dynamic sleep patch | Experimental local compile passed, but review found unsafe wake and ISR behavior; patch is excluded from the branch workflow |
| Normal application update image | PXL 0.2 baseline and PM-only branch builds generated distinct application and factory images; PXL 0.3 pending |
| Release publication | None |

The build targets only `heltec-v3`. The PM framework is pinned through that
board's PlatformIO configuration. The official Meshtastic radio protocol,
routing, encryption, region tables, and transmit power limits are not patched.
The current branch artifact still identifies itself as PXL 0.2 and does not
release the PM sleep lock. It is not a low-power PXL 0.3 firmware.

## Device test gate

All cases below are **untested** until run on a physical Heltec V3:

1. Back up the device configuration. Install `*-update.bin` using a normal
   firmware update without full erase. Confirm NodeDB, channels, keys, RU
   region, and user settings survive; keep the factory image separate.
2. With the screen on, after screen timeout, and after the power FSM enters
   light sleep, perform at least 20 short USER presses per condition. Record
   missed presses, duplicate frame changes, first-press wake behavior, and
   whether a long hold is ever required.
3. Test long, double, multiple, and shutdown press actions supported by the
   current device configuration. Watch for accidental short actions during a
   long or multiple press. Record results with and without USB connected.
4. Verify LoRa receive, transmit, and forwarding, including packets arriving
   while idle. Verify Bluetooth connection and reconnection, serial API,
   display updates, and several hours of idle operation.
5. Record logs for USER, LoRa DIO1, timer, and communication-stack wake events.
   Check that the node does not miss messages or repeatedly wake without work.
6. Compare PXL 0.2 and 0.3 on the same board and supply at the same voltage,
   display state, Bluetooth/Wi-Fi settings, LoRa settings, and traffic level.
   Record instrument, voltage, sample duration, awake and idle current, and
   energy or runtime. Test Bluetooth enabled and disabled separately.

## Known limits and risks

- Successful compilation and PM SDK flags do not prove that the CPU enters
  light sleep or that battery life improves. No 25 mA or 32-hour claim is made.
- Automatic light sleep depends on the configured power-saving state and on
  other components releasing their own PM locks. Bluetooth may prevent sleep;
  the patch does not forcibly disable it because that could break reconnection.
- The PM-capable Arduino 2.x package is a pinned prebuilt M1NL framework, not
  the default official Meshtastic package. Its archive SHA-256 is checked by
  the workflow, but device behavior still needs validation.
- The USER wake edge, debounce, release event, LoRa IRQ timing, and configuration
  retention require physical testing. A build cannot verify them.
- The first dynamic-sleep draft compiled locally, but review found that
  `gpio_wakeup_enable` changes the regular USER interrupt from CHANGE to a
  level trigger and that RadioLib can disable DIO1 wake after an IRQ. It also
  found a screen command queue race and an entry-state transition race. This
  draft is kept only under ignored local `work/` for investigation and is not
  applied by GitHub Actions.
- Other boards are outside this PXL 0.3 phase. The feature flag and framework
  pin are scoped to Heltec V3.

**Release recommendation:** do not publish a final release. First finish a
safe wake design, then pass the device test gate and current measurements.
