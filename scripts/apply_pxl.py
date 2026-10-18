import argparse
from pathlib import Path
import os
import re


parser = argparse.ArgumentParser()
parser.add_argument("--firmware-dir", type=Path, required=True)
ROOT = parser.parse_args().firmware_dir
PXL_VERSION = os.environ.get("PXL_VERSION", "0.2")


# ====================================================
# Helpers
# ====================================================

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


pending_writes: dict[Path, str] = {}


def write(path: Path, text: str) -> None:
    pending_writes[path] = text


def find_one(pattern, text, name, flags=0):
    regex = re.compile(pattern, flags)
    matches = list(regex.finditer(text))

    if len(matches) != 1:
        raise RuntimeError(
            f"{name}: expected exactly one match, "
            f"found {len(matches)}"
        )

    return matches[0]


def set_jsonc_pref(text, key, value):
    pattern = re.compile(
        rf'(?m)^'
        rf'(?P<indent>[ \t]*)'
        rf'(?://[ \t]*)?'
        rf'"{re.escape(key)}"'
        rf'[ \t]*:[ \t]*'
        rf'.*?,'
        rf'[ \t]*$'
    )

    matches = list(pattern.finditer(text))

    if len(matches) != 1:
        raise RuntimeError(
            f"userPrefs.jsonc: {key}: "
            f"expected exactly one match, "
            f"found {len(matches)}"
        )

    match = matches[0]
    indent = match.group("indent")

    replacement = (
        f'{indent}"{key}": {value},'
    )

    return (
        text[:match.start()]
        + replacement
        + text[match.end():]
    )


# ====================================================
# 1. userPrefs.jsonc
#
# OEM trigger + blank OEM bitmap + OLED_RU
# ====================================================

prefs_path = ROOT / "userPrefs.jsonc"
prefs = read(prefs_path)

prefs = set_jsonc_pref(
    prefs,
    "USERPREFS_OEM_TEXT",
    '"PXL Mesh"'
)

prefs = set_jsonc_pref(
    prefs,
    "USERPREFS_OEM_FONT_SIZE",
    '"0"'
)

prefs = set_jsonc_pref(
    prefs,
    "USERPREFS_OEM_IMAGE_WIDTH",
    '"1"'
)

prefs = set_jsonc_pref(
    prefs,
    "USERPREFS_OEM_IMAGE_HEIGHT",
    '"1"'
)

prefs = set_jsonc_pref(
    prefs,
    "USERPREFS_OEM_IMAGE_DATA",
    '"{ 0x00 }"'
)


# OLED_RU is not present in the stock userPrefs file.
# userPrefs keys become compiler definitions, so this gives:
#
#   -DOLED_RU=true
#
# for every target in the matrix.

oled_pattern = re.compile(
    r'(?m)^'
    r'(?P<indent>[ \t]*)'
    r'(?://[ \t]*)?'
    r'"OLED_RU"'
    r'[ \t]*:[ \t]*'
    r'.*?,'
    r'[ \t]*$'
)

oled_matches = list(oled_pattern.finditer(prefs))

if len(oled_matches) == 1:
    match = oled_matches[0]

    prefs = (
        prefs[:match.start()]
        + f'{match.group("indent")}"OLED_RU": "true",'
        + prefs[match.end():]
    )

elif len(oled_matches) == 0:

    marker = find_one(
        r'(?m)^'
        r'(?P<indent>[ \t]*)'
        r'"USERPREFS_OEM_IMAGE_DATA"'
        r'[ \t]*:[ \t]*'
        r'.*?,'
        r'[ \t]*$',
        prefs,
        "OEM image data preference"
    )

    indent = marker.group("indent")

    prefs = (
        prefs[:marker.end()]
        + "\n"
        + f'{indent}"OLED_RU": "true",'
        + prefs[marker.end():]
    )

else:
    raise RuntimeError(
        "userPrefs.jsonc: OLED_RU is not unique"
    )


write(prefs_path, prefs)


# ====================================================
# 2. Screen.cpp
# ====================================================

screen_path = ROOT / "src/graphics/Screen.cpp"
screen = read(screen_path)


# ----------------------------------------------------
# Extra static frame capacity
# ----------------------------------------------------

match = find_one(
    r'(?m)^'
    r'(?P<prefix>[ \t]*'
    r'#define[ \t]+'
    r'NUM_EXTRA_FRAMES[ \t]+)'
    r'(?P<count>\d+)'
    r'(?P<rest>.*)$',
    screen,
    "NUM_EXTRA_FRAMES"
)

old_count = int(match.group("count"))
new_count = old_count + 1

replacement = (
    match.group("prefix")
    + str(new_count)
    + match.group("rest")
)

screen = (
    screen[:match.start()]
    + replacement
    + screen[match.end():]
)

print(
    f"NUM_EXTRA_FRAMES: "
    f"{old_count} -> {new_count}"
)


# ----------------------------------------------------
# Shorter boot
# ----------------------------------------------------

match = find_one(
    r'(?m)^'
    r'(?P<indent>[ \t]*)'
    r'uint32_t[ \t]+'
    r'logo_timeout'
    r'[ \t]*=[ \t]*'
    r'\d+'
    r'[ \t]*;'
    r'.*$',
    screen,
    "logo_timeout"
)

screen = (
    screen[:match.start()]
    + match.group("indent")
    + "uint32_t logo_timeout = 2500; "
    + "// PXL: ~2.5s stock + ~2.5s OEM stage"
    + screen[match.end():]
)


# ----------------------------------------------------
# Replace stock OEM frame with PXL boot
# ----------------------------------------------------

match = find_one(
    r'static[ \t]+'
    r'FrameCallback[ \t]+'
    r'bootOEMFrames\[\]'
    r'[ \t]*=[ \t]*'
    r'\{'
    r'graphics::UIRenderer::drawOEMBootScreen'
    r'\}'
    r'[ \t]*;',
    screen,
    "OEM boot callback"
)

screen = (
    screen[:match.start()]
    + "static FrameCallback bootOEMFrames[] = "
    + "{graphics::DebugRenderer::drawPxlBootScreen};"
    + screen[match.end():]
)


# ----------------------------------------------------
# Smooth boot animation on non-EInk displays
# ----------------------------------------------------

match = find_one(
    r'(?m)^'
    r'(?P<indent>[ \t]*)'
    r'uint32_t[ \t]+'
    r'desiredFramerate'
    r'[ \t]*=[ \t]*'
    r'IDLE_FRAMERATE'
    r'[ \t]*;'
    r'[ \t]*$',
    screen,
    "desiredFramerate"
)

fps_patch = (
    match.group(0)
    + "\n\n"
    + "#if defined(USERPREFS_OEM_TEXT) "
      "&& !defined(USE_EINK)\n"
    + "    // Smooth PXL boot animation only "
      "while the OEM boot stage is active.\n"
    + "    if (showingBootScreen "
      "&& !showingOEMBootScreen) {\n"
    + "        desiredFramerate = 12;\n"
    + "    }\n"
    + "#endif"
)

screen = (
    screen[:match.start()]
    + fps_patch
    + screen[match.end():]
)


# ----------------------------------------------------
# Add PXL STATUS to normal frames
# ----------------------------------------------------

match = find_one(
    r'(?m)^'
    r'(?P<indent>[ \t]*)'
    r'if[ \t]*'
    r'\([ \t]*'
    r'!hiddenFrames\.system'
    r'[ \t]*\)'
    r'[ \t]*\{',
    screen,
    "system frame insertion point"
)

indent = match.group("indent")

pxl_frame = (
    f"{indent}// PXL custom status screen\n"
    f"{indent}normalFrames[numframes++] = "
    f"graphics::DebugRenderer::drawPxlStatus;\n"
    f"{indent}indicatorIcons.push_back(icon_system);\n"
    f"\n"
)

screen = (
    screen[:match.start()]
    + pxl_frame
    + screen[match.start():]
)


write(screen_path, screen)


# ====================================================
# 3. DebugRenderer.h
# ====================================================

header_path = (
    ROOT
    / "src/graphics/draw/DebugRenderer.h"
)

header = read(header_path)

match = find_one(
    r'(?m)^'
    r'(?P<indent>[ \t]*)'
    r'void[ \t]+'
    r'drawSystemScreen'
    r'[ \t]*\(',
    header,
    "drawSystemScreen declaration"
)

indent = match.group("indent")

declarations = (
    f"{indent}// PXL custom screens\n"
    f"{indent}void drawPxlBootScreen("
    f"OLEDDisplay *display, "
    f"OLEDDisplayUiState *state, "
    f"int16_t x, int16_t y);\n"
    f"{indent}void drawPxlStatus("
    f"OLEDDisplay *display, "
    f"OLEDDisplayUiState *state, "
    f"int16_t x, int16_t y);\n"
    f"\n"
)

header = (
    header[:match.start()]
    + declarations
    + header[match.start():]
)

write(header_path, header)


# ====================================================
# 4. DebugRenderer.cpp
# ====================================================

renderer_path = (
    ROOT
    / "src/graphics/draw/DebugRenderer.cpp"
)

renderer = read(renderer_path)


# strncmp used for compact CLIENT_* role names.

if "#include <cstring>" not in renderer:

    include_match = find_one(
        r'(?m)^'
        r'#include[ \t]+'
        r'<target_specific\.h>'
        r'[ \t]*$',
        renderer,
        "target_specific include"
    )

    renderer = (
        renderer[:include_match.start()]
        + "#include <cstring>\n"
        + renderer[include_match.start():]
    )


match = find_one(
    r'(?m)^'
    r'void[ \t]+'
    r'drawSystemScreen'
    r'[ \t]*\(',
    renderer,
    "drawSystemScreen implementation"
)


pxl_screens = r'''
// ****************************
// *      PXL BOOT            *
// ****************************
void drawPxlBootScreen(OLEDDisplay *display, OLEDDisplayUiState *state, int16_t x, int16_t y)
{
    static uint32_t startedAt = 0;

    if (startedAt == 0) {
        startedAt = millis();
    }

    const uint32_t elapsed = millis() - startedAt;

    display->clear();
    display->setTextAlignment(TEXT_ALIGN_CENTER);

    const bool compact = SCREEN_HEIGHT <= 64;

    const int centerX = x + (SCREEN_WIDTH / 2);

    const int logoY =
        y + (compact ? 8 : (SCREEN_HEIGHT / 2) - 26);

    const int meshY =
        y + (compact ? 27 : (SCREEN_HEIGHT / 2) - 4);

    display->setFont(FONT_MEDIUM);
    display->drawString(
        centerX,
        logoY,
        "PXL"
    );

    display->setFont(FONT_SMALL);
    display->drawString(
        centerX,
        meshY,
        "MESH"
    );


    // Progress bar
    const int barW = (SCREEN_WIDTH * 2) / 3;
    const int barH = compact ? 6 : 8;

    const int barX =
        x + (SCREEN_WIDTH - barW) / 2;

    const int barY =
        y + SCREEN_HEIGHT - (compact ? 22 : 30);

    const int innerW = barW - 2;

    display->drawRect(
        barX,
        barY,
        barW,
        barH
    );


    // E-Ink gets a static complete bar.
    // OLED/TFT gets the animation.
    int fillW = innerW;

#ifndef USE_EINK
    fillW =
        (elapsed * innerW) / 2400;

    if (fillW < 0) {
        fillW = 0;
    }

    if (fillW > innerW) {
        fillW = innerW;
    }
#endif

    if (fillW > 0) {
        display->fillRect(
            barX + 1,
            barY + 1,
            fillW,
            barH - 2
        );
    }


    // Small PXL firmware version
    display->setFont(FONT_SMALL);
    display->setTextAlignment(TEXT_ALIGN_RIGHT);

    display->drawString(
        x + SCREEN_WIDTH - 2,
        y + SCREEN_HEIGHT - (compact ? 12 : 17),
        "__PXL_VERSION__"
    );

    display->setTextAlignment(TEXT_ALIGN_LEFT);
}


// ****************************
// *      PXL STATUS          *
// ****************************
void drawPxlStatus(OLEDDisplay *display, OLEDDisplayUiState *state, int16_t x, int16_t y)
{
    display->clear();
    display->setTextAlignment(TEXT_ALIGN_LEFT);
    display->setFont(FONT_SMALL);

    graphics::drawCommonHeader(
        display,
        x,
        y,
        "PXL STATUS"
    );

    char line[32];


    // Extra spacing below Meshtastic header
    const int firstY =
        (SCREEN_HEIGHT <= 64)
            ? 17
            : getTextPositions(display)[1];

    const int lineStep =
        (SCREEN_HEIGHT <= 64)
            ? 9
            : (FONT_HEIGHT_SMALL + 2);

    int textY = firstY;


    // Battery
    if (powerStatus->getHasBattery()) {
        snprintf(
            line,
            sizeof(line),
            "BAT %d%%  %.2fV",
            powerStatus->getBatteryChargePercent(),
            powerStatus->getBatteryVoltageMv() / 1000.0f
        );
    } else {
        snprintf(
            line,
            sizeof(line),
            "BAT USB"
        );
    }

    display->drawString(
        x,
        textY,
        line
    );

    textY += lineStep;


    // Nodes
    snprintf(
        line,
        sizeof(line),
        "NODES %d/%d",
        nodeStatus->getNumOnline(),
        nodeStatus->getNumTotal()
    );

    display->drawString(
        x,
        textY,
        line
    );

    textY += lineStep;


    // Channel utilization / own TX airtime
    snprintf(
        line,
        sizeof(line),
        "CH %.1f%%  TX %.1f%%",
        airTime->channelUtilizationPercent(),
        airTime->utilizationTXPercent()
    );

    display->drawString(
        x,
        textY,
        line
    );

    textY += lineStep;


    // Compact device role
    const char *role =
        DisplayFormatters::getDeviceRole(
            config.device.role
        );

    const char *shortRole = role;

    if (
        role != nullptr
        && strncmp(
            role,
            "CLIENT_",
            7
        ) == 0
    ) {
        shortRole = role + 7;
    }

    snprintf(
        line,
        sizeof(line),
        "ROLE %s",
        shortRole != nullptr
            ? shortRole
            : "UNKNOWN"
    );

    display->drawString(
        x,
        textY,
        line
    );


    graphics::drawCommonFooter(
        display,
        x,
        y
    );
}


'''

pxl_screens = pxl_screens.replace(
    "__PXL_VERSION__",
    f"PXL {PXL_VERSION}"
)


renderer = (
    renderer[:match.start()]
    + pxl_screens
    + renderer[match.start():]
)

write(renderer_path, renderer)


# ====================================================
# Verification
# ====================================================

required_strings = {
    "PXL boot callback":
        "DebugRenderer::drawPxlBootScreen",

    "PXL status callback":
        "DebugRenderer::drawPxlStatus",

    "PXL boot renderer":
        "void drawPxlBootScreen",

    "PXL status renderer":
        "void drawPxlStatus",

    "OLED RU":
        '"OLED_RU": "true"',

    "PXL OEM":
        '"USERPREFS_OEM_TEXT": "PXL Mesh"',
}


combined = (
    pending_writes[screen_path]
    + pending_writes[header_path]
    + pending_writes[renderer_path]
    + pending_writes[prefs_path]
)


for name, value in required_strings.items():
    if value not in combined:
        raise RuntimeError(
            f"Verification failed: {name}"
        )

for path, text in pending_writes.items():
    path.write_text(text, encoding="utf-8")


print()
print("========================================")
print(f"PXL Meshtastic {PXL_VERSION}")
print("========================================")
print("+ OLED_RU")
print("+ PXL animated boot")
print("+ PXL version branding")
print("+ PXL STATUS")
print("+ compact role display")
print("+ shorter boot")
print("+ E-Ink safe static boot")
print("+ radio stack unchanged")
print("+ regional limits unchanged")
print("+ power limits unchanged")
print("========================================")
