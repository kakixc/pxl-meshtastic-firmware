"""Fail the Heltec V3 build unless its installed ESP32-S3 SDK supports PM."""

import argparse
from pathlib import Path


REQUIRED = (
    "CONFIG_PM_ENABLE=y",
    "CONFIG_FREERTOS_USE_TICKLESS_IDLE=y",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework-dir", type=Path, required=True)
    args = parser.parse_args()

    sdkconfig = args.framework_dir / "tools" / "sdk" / "esp32s3" / "sdkconfig"
    if not sdkconfig.is_file():
        parser.error(f"ESP32-S3 sdkconfig not found: {sdkconfig}")

    lines = set(sdkconfig.read_text(encoding="utf-8").splitlines())
    missing = [flag for flag in REQUIRED if flag not in lines]
    if missing:
        parser.error(f"ESP32-S3 framework lacks: {', '.join(missing)}")

    print(f"Verified ESP32-S3 framework: {args.framework_dir.resolve()}")
    for flag in REQUIRED:
        print(flag)


if __name__ == "__main__":
    main()
