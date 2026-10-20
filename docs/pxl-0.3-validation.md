# PXL 0.3 Heltec V3 validation

PXL 0.3 is an experimental Heltec V3 project based on official Meshtastic
`v2.7.26.54e0d8d`. A compiled experimental image exists; a validated release
is not ready. This document
separates build evidence from device behavior. No Heltec V3 or current meter
was available for this validation.

## Software evidence

| Check | Result |
| --- | --- |
| Official tag and retained PXL 0.2 display patch | Local build and manual Actions baseline passed |
| PM-capable Arduino 2.x framework, ESP32-S3 | `CONFIG_PM_ENABLE=y` and `CONFIG_FREERTOS_USE_TICKLESS_IDLE=y` verified; local build and [manual Actions run](https://github.com/kakixc/pxl-meshtastic-firmware/actions/runs/38999865180) passed |
| Checksum-verified archive used by compiler | [Manual Actions run](https://github.com/kakixc/pxl-meshtastic-firmware/actions/runs/39001031077) passed after PlatformIO installed the downloaded and SHA-256-checked local archive |
| Full PXL 0.3 dynamic sleep patch | The RTC EXT0/EXT1 prototype applied to the exact official tag and [opt-in manual Actions run 39424790633](https://github.com/kakixc/pxl-meshtastic-firmware/actions/runs/39424790633) compiled it. The default workflow still omits it; runtime wake behavior is unverified |
| Heltec V3 short USER press with screen off | A board-guarded source patch queues the frame change after screen-on; [manual Actions run 39093316580](https://github.com/kakixc/pxl-meshtastic-firmware/actions/runs/39093316580) compiled and packaged it. Device behavior is pending |
| Heltec V3 USER polling after ordinary Light Sleep | Candidate schedules an immediate OneButton poll and prevents the current loop from delaying if USER is still held after the regular ISR is reattached. [Manual Actions run 39094022238](https://github.com/kakixc/pxl-meshtastic-firmware/actions/runs/39094022238) compiled the final revision; device behavior is pending |
| Normal application update image | [Opt-in run 39424790633](https://github.com/kakixc/pxl-meshtastic-firmware/actions/runs/39424790633) contains distinct `PXL.3-experimental-update.bin` (2,140,896 bytes, SHA-256 `d9607319d94fdf94341e176105cfaa47371084e7a75424ae6cb0a01badb208cc`) and factory image; both checksum files match. Configuration retention on a device is pending |
| Release publication | None |

Run `39093316580` produced `PXL.2-update.bin` (2,137,360 bytes,
SHA-256 `7408e7f7f6b1c760918e7c2e8bb0a9cfcb3f8f6abcabc665135cd70517616ece`)
and a separate factory image (2,202,896 bytes). Both packaged checksum files
matched the downloaded images. The update is an application image; preserving
configuration still requires a normal update test on a device.

The button candidate, run `39094022238` at commit `b9dccae`, produced
`PXL.2-update.bin` (2,137,408 bytes, SHA-256
`1e56618f4c780f29808c42b1d05035a77f3a99d0de5f90163871f091948084d3`)
and a separate factory image (2,202,944 bytes, SHA-256
`aa53b4183c441d52e2ec7b2008b4e64902273d1990f4a4f755aa2a2bb33a247f`).
Both matched their packaged checksum files. Neither image enables automatic
light sleep or proves the button behavior on hardware.

The latest default PXL 0.2 build, run `39423453321` at commit `1866fe1`, produced
`PXL.2-update.bin` (2,137,440 bytes, SHA-256
`3ab440d36a45860405dab6e8c5d50e3d25fa0c78dd5bb6401dd8f742780ed132`)
and a separate factory image (2,202,976 bytes, SHA-256
`866e21676c590b3fc8ccb4e6447e688f034c099ce479eefef9713564b803f497`).
The downloaded checksum files matched. It includes the PXL STATUS width
guard but not Dynamic Light Sleep.

The opt-in PXL 0.3 run at commit `95ecb1e` produced a separate factory image
of 2,206,432 bytes (SHA-256
`a01bd86cdfca58a263162a9479102b364ec1040e855cc775a27b65662cf42821`).
Both downloaded checksums matched. `esptool image-info` identified the update
as an ESP32-S3 application image with valid checksum and validation hash.
The build targets only `heltec-v3`. The PM framework is pinned through that
board's PlatformIO configuration. The official Meshtastic radio protocol,
routing, encryption, region tables, and transmit power limits are not patched.
The default workflow artifact remains PXL 0.2 without automatic sleep. The
opt-in PXL 0.3 image is an unvalidated test candidate, not a release.

## M1NL and upstream PR port inventory

| Mechanism | Status on official 2.7.26 in this branch |
| --- | --- |
| PM-capable Arduino 2.x framework for Heltec V3 | Pinned, hash-verified, compiled |
| PXL 0.2 animation, STATUS, Cyrillic, shorter boot | Retained and compiled |
| USER off-screen frame queue and prompt poll after ordinary Light Sleep | Heltec V3-only candidates; device behavior untested |
| Automatic light sleep and `ESP_PM_NO_LIGHT_SLEEP` state control | Compiled in opt-in experimental CI artifact; excluded from default build |
| RTC USER/DIO1 wake, pin restoration, repeated radio IRQ handling | Source port compiled; physical wake and repeated IRQ behavior not verified |
| M1NL GPS, radio, serial, and Bluetooth interactions with automatic sleep | Not ported or verified |
| M1NL 32 kHz slow-clock setup and PR #11702 DFS/Wi-Fi power saving | Not ported; board and framework behavior unverified |

This inventory is selective by design: the [M1NL proposal](https://github.com/meshtastic/firmware/pull/7121)
targets another firmware revision, and [PR #11702](https://github.com/meshtastic/firmware/pull/11702)
is a draft against later `develop`. Copying either entire tree would replace
the required official 2.7.26 base.

## RTC prototype compile evidence

`patches/heltec-v3-dynamic-sleep.patch` is an **experimental source patch**,
applied only when the manual workflow's `experimental_dynamic_sleep` input is
true. It
uses the verified PM-capable Arduino 2.x framework, RTC EXT1 active-low wake
for USER GPIO0, and RTC EXT0 active-high wake for DIO1 GPIO14. It restores
only these two RTC pins, reattaches the normal button ISR, and calls the
official `RadioLibInterface::pollMissedIrqs()` after an EXT0 wake to check a
latched RX_DONE. It leaves radio protocol and IRQ flag definitions unchanged.

The patch passed `git apply --check` against the official tag, including after
the separate framework pin. Local PlatformIO Heltec V3 builds passed for the
initial RTC version (329.42 seconds), immediate RX_DONE polling (90.41
seconds), and a guard that refuses sleep during an active LoRa transmission
(85.52 seconds). The final prototype generated an application image of
2,140,928 bytes and a factory image of 2,206,464 bytes under ignored local
`work/`. A fourth local build with a 25 ms power-FSM interval in LS also
passed in 178.65 seconds and generated a 2,140,944-byte application image.
The RTC level-guard revision also compiled in 263.30 seconds and generated a
2,141,120-byte application image; it has not been packaged by Actions.
These are compile results, not runtime validation or a PXL 0.3 release.

Remaining questions before considering this patch for a default build or release:

- Meshtastic's power FSM runs on a roughly 100 ms scheduled callback. A brief
  USER press may be released before it handles the RTC wake. The wake reason
  can turn on the screen, but the OneButton classifier cannot reconstruct a
  missed press/release pair or reliably distinguish it from a multi-press.
- The current experimental patch schedules the power FSM every 25 ms while
  Heltec V3 is in its light-sleep state, leaving other states at 100 ms.
  This narrows the nominal wake-handling window but increases periodic CPU
  activity. Its effect on current draw and very short presses is unmeasured.
- `esp_sleep_get_wakeup_cause()` may retain a previous wake reason when PM
  does not actually enter automatic sleep. The RTC prototype needs a reliable
  per-cycle wake indication before reacting to repeated EXT0/EXT1 reasons.
- The candidate vetoes sleep while RadioLib reports an active transmission;
  its immediate radio backup handles a latched RX_DONE. It does not prove that
  TX_DONE races, consecutive packets, Bluetooth reconnection, or serial API
  work through this sleep path. The wake-to-dispatch latency needs a board
  trace.
- The PM lock and RTC configuration error paths need a target-board fail-awake
  check. USB and battery runs may behave differently because other PM locks
  can suppress automatic sleep.

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
- M1NL's `gpioReset()` iterates over every RTC-capable and output GPIO. A
  Heltec V3 port should restore only the pins and holds it changes; broad
  restoration can disturb unrelated board peripherals.
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

### Automatic-wake scheduling found in official 2.7.26

`RadioLibInterface` inherits `NotifiedWorkerThread`, but that worker is an
`OSThread` registered with `mainController`; it is not a separate FreeRTOS
task. The main `loop()` calls `esp32Loop()`, checks power commands, polls missed
radio IRQs at most once per second, processes input, and only then runs
`mainController`. It can then block on `mainDelay`'s FreeRTOS semaphore until a
scheduled thread is due. Normal USER and DIO1 edge ISRs notify that semaphore.

ESP-IDF 4.4 says automatic Light Sleep gates peripheral interrupts. RTC
EXT0/EXT1 can wake the chip, but that wake does not itself notify Meshtastic's
semaphore. The main loop may therefore remain blocked until its next timeout;
the actual delay depends on the nearest scheduled task. Once it runs, any RTC
pin restoration in `esp32Loop()` precedes `mainController` callbacks, but a
short USER press may already have ended, and the once-per-second radio backup
poll is not an immediate DIO1 dispatch. This is a source-level risk analysis,
not an observed device failure. See the [ESP-IDF 4.4 power management
reference](https://docs.espressif.com/projects/esp-idf/en/v4.4/esp32s3/api-reference/system/power_management.html).

The next runtime candidate needs a bounded wake-to-dispatch path that restores
only USER GPIO0 and DIO1 GPIO14 before ordinary digital reads, then lets
OneButton classify the still-held button and RadioLib process the latched IRQ.
It must establish what happens when USER is released before dispatch and when
DIO1 remains high across consecutive packets. A timer used solely to poll for
RTC wake could materially reduce the intended power savings, so its current
cost must be measured before adoption.

The experimental port also differs from M1NL's power policy: M1NL configures
20 MHz minimum CPU frequency when dynamic frequency scaling is available,
whereas the current Heltec V3 prototype holds 80 MHz to stay aligned with the
official tag's normal CPU setting. Thus even successful automatic sleep would
not prove equivalent power use. Lowering the minimum needs UART, radio timing,
Bluetooth, and current tests on the target board; it is not a safe numerical
change to make from a compiler result alone.

The tracked RTC prototype now requires the current USER GPIO0 or DIO1 GPIO14
level to match EXT1/EXT0 before acting on a stored wake cause. It applied to a
fresh exact-tag checkout and compiled locally in 263.30 seconds. This narrows
false wake handling; it cannot recover a short USER press already released or
establish that RX_DONE is reliably handled after repeated radio wakes.

## PXL display patch review

The retained PXL 0.2 patcher compiles on the exact official tag and keeps the
boot animation, shorter boot stage, Cyrillic setting, and PXL STATUS:

- `scripts/apply_pxl.py` now collects and verifies all four edited contents
  before writing. A missing last-file anchor was checked against a disposable
  exact-tag checkout and left all four source files untouched.
- The PXL STATUS frame uses the same `icon_system` marker as the next stock
  system frame. Consider a distinct indicator and verify it on the 128×64 OLED.
- PXL STATUS now checks rendered width for each of its four rows (battery,
  nodes, channel/TX utilization, role) before drawing. The patcher applied to
  a clean exact-tag checkout, and the final Heltec V3 incremental build passed
  in 80.42 seconds. Shortened values end in an ellipsis; inspection on a
  128×64 OLED is still pending.
- The version placeholder is replaced once in the current patcher. An older
  review note about a duplicate replacement was stale.

### PXL function audit and improvement candidates

The source-level inventory is `OLED_RU`, the PXL OEM boot frame and animation,
version branding, a shorter stock boot stage, PXL STATUS, and compact role
names. The exact-tag build verifies they compile together; none has been
visually checked on the Heltec V3 OLED in this session. The button patch is a
separate Heltec V3 change, also awaiting device testing.

For the device pass, time the stock and PXL boot stages and check progress-bar
motion, version text, and an ordinary restart. Display a Russian node name and
message to inspect Cyrillic glyphs. Visit PXL STATUS on battery and USB,
verify that battery voltage, node count, channel use, TX use, and role agree
with Meshtastic's app, and exercise values long enough to show an ellipsis.
Move forward and backward through neighboring frames and confirm that the
STATUS indicator is understandable. Repeat screen navigation with the display
already off and after a sleep/wake cycle.

1. **Before PXL 0.3 release:** check battery and airtime extremes on the OLED
   and verify that the STATUS ellipsis is legible. If not, switch to a compact
   numeric format that retains the complete value.
2. **Before PXL 0.3 release:** validate USER tap, hold, double/multiple press,
   screen-off wake, and a tap during sleep on a real Heltec V3. Compare with
   stock 2.7.26 to detect changed long-press actions.
3. **Useful UI follow-up:** give PXL STATUS a distinct frame indicator. It
   currently reuses `icon_system`, so two adjacent frames look identical in
   the indicator strip.
4. **Useful diagnostics follow-up:** show last wake reason and counted sleep
   entries in a debug view. This would make it possible to tell actual sleep
   from a PM-capable build that remains awake due to another PM lock. Keep
   diagnostic updates out of the hot radio path.
5. **Useful boot follow-up:** confirm that the static animation start time is
   reset if the UI is restarted without rebooting the chip; only change it if
   that case is reproducible.

### Hop-delivery investigation

Official 2.7.26 already implements hop limits, duplicate/retransmission
handling, rebroadcast roles, traceroute with per-hop SNR, and a radio backup
poll for missed RX_DONE interrupts. PXL 0.3 leaves those mechanisms unchanged.
The Dynamic Light Sleep prototype can plausibly lose or delay an RX_DONE wake;
that would appear to users as worse delivery through hops even though the
routing code is untouched.

The official default hop limit is `HOP_RELIABLE` (3), with a hard maximum of
7. Blindly raising it can add rebroadcast airtime and congestion, so the first
practical improvement is to identify the failing hop with traceroute and check
relay role/rebroadcast settings. A useful PXL-only feature would summarize
recent route/SNR and ACK failures on a diagnostic screen using existing packet
metadata, without changing how packets are sent.

Use at least three nodes (source, relay, destination) and compare official
2.7.26, PXL 0.2, and the PXL 0.3 candidate with identical channel, role,
placement, power, and hop-limit settings. Send a fixed sequence of direct and
two-hop acknowledged messages and record delivery count, ACK latency,
traceroute path/SNR, channel/TX utilization, missed RX_DONE logs, and current
draw. Repeat with display and Bluetooth in their intended usage states. A
software-only build cannot establish that relay delivery has improved. If
losses occur only in the sleep candidate, fix the radio wake path before
considering any change to official routing or rebroadcast policy. Any later
routing change needs a separate proposal and measured comparison.

**Release recommendation:** do not publish a final release. First finish a
safe wake design, then pass the device test gate and current measurements.
