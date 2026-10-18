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
| Checksum-verified archive used by compiler | [Manual Actions run](https://github.com/kakixc/pxl-meshtastic-firmware/actions/runs/39001031077) passed after PlatformIO installed the downloaded and SHA-256-checked local archive |
| Full PXL 0.3 dynamic sleep patch | Experimental local compile passed, but review found unsafe wake and ISR behavior; patch is excluded from the branch workflow |
| Heltec V3 short USER press with screen off | A board-guarded source patch queues the frame change after screen-on; [manual Actions run 39093316580](https://github.com/kakixc/pxl-meshtastic-firmware/actions/runs/39093316580) compiled and packaged it. Device behavior is pending |
| Heltec V3 USER polling after ordinary Light Sleep | Candidate schedules an immediate OneButton poll and prevents the current loop from delaying if USER is still held after the regular ISR is reattached. [Manual Actions run 39094022238](https://github.com/kakixc/pxl-meshtastic-firmware/actions/runs/39094022238) compiled the final revision; device behavior is pending |
| Normal application update image | PM-only CI artifact contains distinct `PXL.2-update.bin` (2,137,296 bytes, SHA-256 `bb14fd2588461a3a6c1f8e2cde253272c07f9edf71c71de332ea299e08e93649`) and factory image; both checksum files match. PXL 0.3 pending |
| Release publication | None |

Run `39093316580` produced `PXL.2-update.bin` (2,137,360 bytes,
SHA-256 `7408e7f7f6b1c760918e7c2e8bb0a9cfcb3f8f6abcabc665135cd70517616ece`)
and a separate factory image (2,202,896 bytes). Both packaged checksum files
matched the downloaded images. The update is an application image; preserving
configuration still requires a normal update test on a device.

The latest candidate, run `39094022238` at commit `b9dccae`, produced
`PXL.2-update.bin` (2,137,408 bytes, SHA-256
`1e56618f4c780f29808c42b1d05035a77f3a99d0de5f90163871f091948084d3`)
and a separate factory image (2,202,944 bytes, SHA-256
`aa53b4183c441d52e2ec7b2008b4e64902273d1990f4a4f755aa2a2bb33a247f`).
Both matched their packaged checksum files. Neither image enables automatic
light sleep or proves the button behavior on hardware.

The build targets only `heltec-v3`. The PM framework is pinned through that
board's PlatformIO configuration. The official Meshtastic radio protocol,
routing, encryption, region tables, and transmit power limits are not patched.
The current branch artifact still identifies itself as PXL 0.2 and does not
enable automatic light sleep. It is not a low-power PXL 0.3 firmware.

## M1NL and upstream PR port inventory

| Mechanism | Status on official 2.7.26 in this branch |
| --- | --- |
| PM-capable Arduino 2.x framework for Heltec V3 | Pinned, hash-verified, compiled |
| PXL 0.2 animation, STATUS, Cyrillic, shorter boot | Retained and compiled |
| USER off-screen frame queue and prompt poll after ordinary Light Sleep | Heltec V3-only candidates; device behavior untested |
| Automatic light sleep and `ESP_PM_NO_LIGHT_SLEEP` state control | Experimental local compile only; excluded from CI artifact |
| RTC USER/DIO1 wake, pin restoration, repeated radio IRQ handling | Investigated; no safe 2.7.26 runtime port yet |
| M1NL GPS, radio, serial, and Bluetooth interactions with automatic sleep | Not ported or verified |
| M1NL 32 kHz slow-clock setup and PR #11702 DFS/Wi-Fi power saving | Not ported; board and framework behavior unverified |

This inventory is selective by design: the [M1NL proposal](https://github.com/meshtastic/firmware/pull/7121)
targets another firmware revision, and [PR #11702](https://github.com/meshtastic/firmware/pull/11702)
is a draft against later `develop`. Copying either entire tree would replace
the required official 2.7.26 base.

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
- If a short USER press ends before normal code resumes after Light Sleep,
  polling cannot reconstruct its full timing. The candidate must be tested
  with varied press lengths and repeated presses before treating it as a fix.
- The first dynamic-sleep draft compiled locally, but review found that
  `gpio_wakeup_enable` changes the regular USER interrupt from CHANGE to a
  level trigger and that RadioLib can disable DIO1 wake after an IRQ. It also
  found a screen command queue race and an entry-state transition race. This
  draft is kept only under ignored local `work/` for investigation and is not
  applied by GitHub Actions.
- ESP-IDF 4.4.7 says RTC EXT0/EXT1 wake leaves their pins in RTC mode until
  `rtc_gpio_deinit()` is called, and EXT1 may require clearing pad hold too.
  The installed Arduino 2.x headers offer no general automatic-wake callback
  to restore USER and DIO1 before their ordinary interrupt handlers run.
- Other boards are outside this PXL 0.3 phase. The feature flag and framework
  pin are scoped to Heltec V3.

## RTC wake path to investigate

The M1NL branch uses RTC EXT1 (active low) for Heltec V3 USER on GPIO0 and
RTC EXT0 (active high) for SX1262 DIO1 on GPIO14. Both pins are RTC capable.
This is the next candidate because it avoids changing the digital GPIO
interrupt type used by the button's `CHANGE` ISR and the radio ISR. It is a
design candidate, not a verified fix on official 2.7.26.

Before enabling automatic sleep, the Heltec V3-specific implementation must:

1. Configure RTC wake without replacing the ordinary button/radio edge ISRs;
   check every `esp_err_t`, and retain the `ESP_PM_NO_LIGHT_SLEEP` lock when
   setup fails. Never request an FSM transition inside `lsEnter`.
2. Establish how RTC GPIO hold, pin mux, pulls, and wake-source cleanup are
   restored after **each** automatic wake. M1NL's reset path runs when its
   application lock is reacquired, which may be later than the first code that
   handles a wake event. This timing needs a trace on the target board.
3. Check held-button and held-DIO1 behavior so level wake does not cause a
   rapid wake loop. Verify that release edges still reach the normal debounce
   logic and that RadioLib can process consecutive packets.
4. Queue screen-on before next-frame for a short USER press from an off screen,
   while preserving the existing long and multiple-press state machine.
5. Check timer, serial API, Bluetooth/Wi-Fi PM locks, and USB-connected cases.
   Record actual sleep entry/wake causes and current before claiming savings.

The upstream sleep API reference is the [ESP-IDF 4.4.7 ESP32-S3 sleep modes
documentation](https://docs.espressif.com/projects/esp-idf/en/v4.4.7/esp32s3/api-reference/system/sleep_modes.html).

## PXL display patch review

The retained PXL 0.2 patcher compiles on the exact official tag and keeps the
boot animation, shorter boot stage, Cyrillic setting, and PXL STATUS. Further
improvements can be made after the power path is safe:

- `scripts/apply_pxl.py` now collects and verifies all four edited contents
  before writing. A missing last-file anchor was checked against a disposable
  exact-tag checkout and left all four source files untouched.
- The PXL STATUS frame uses the same `icon_system` marker as the next stock
  system frame. Consider a distinct indicator and verify it on the 128×64 OLED.
- Measure rendered text width for long role names and high node counts before
  drawing PXL STATUS; the fixed `char line[32]` protects memory but does not
  prevent text clipping on the display.
- The version placeholder replacement is called twice consecutively in the
  patcher; one call is sufficient. This is cleanup, not a functional defect.

**Release recommendation:** do not publish a final release. First finish a
safe wake design, then pass the device test gate and current measurements.
