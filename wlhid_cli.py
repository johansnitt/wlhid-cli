#!/usr/bin/env python3
import argparse
import json
import logging
import sys

import wlmouse

POLLING_RATES = {1: 1000, 2: 500, 4: 250, 8: 125, 32: 2000, 64: 4000, 128: 8000}

log = logging.getLogger(__name__)


class PollError(Exception):
    pass


def hex_int(value: str) -> int:
    return int(value, 16)


def read_dpi(dev, profile: int) -> int | None:
    active = wlmouse.query(dev, "dpi", profile)
    if active is None:
        return None
    stages = 6
    dpi_map = wlmouse.query(dev, "dpi map", profile, stages)
    if dpi_map is None:
        return None
    stage = active[1]
    offset = 2 + (stage - 1) * 4
    dpi = int.from_bytes(dpi_map[offset : offset + 2], "big")
    log.debug("stage %d/%d = %d dpi", stage, dpi_map[1], dpi)
    return dpi or None


def read_polling_rate(dev, profile: int) -> int | None:
    rate = wlmouse.query(dev, "polling rate", profile)
    if rate is None:
        return None
    code = rate[1]
    hz = POLLING_RATES.get(code)
    log.debug("code %d = %s hz", code, hz)
    return hz


def read_state(dev) -> dict | None:
    battery = wlmouse.query(dev, "battery")
    if battery is None:
        return None
    charging, level = battery[:2]
    if level > 100:
        return None

    active_profile = wlmouse.query(dev, "profile")
    profile = active_profile[0] if active_profile is not None else None
    log.debug("profile %s", profile)
    dpi = polling_rate = None
    if profile is not None:
        dpi = read_dpi(dev, profile)
        polling_rate = read_polling_rate(dev, profile)

    return {
        "battery_level": level,
        "charging": charging != 0,
        "dpi": dpi,
        "polling_rate": polling_rate,
    }


def read_device(pid: int) -> dict:
    interfaces = wlmouse.interface_paths(pid)
    if not interfaces:
        want = f"{wlmouse.VENDOR_ID:04x}" + (f":{pid:04x}" if pid else "")
        raise PollError("no_device", want)

    error = PollError("no_reply", f"no valid reply from {len(interfaces)} interface(s)")
    for path in interfaces:
        try:
            with wlmouse.open_device(path) as dev:
                state = read_state(dev)
        except OSError as err:
            error = PollError("io_error", err)
            continue
        if state is not None:
            return state
    raise error


def main() -> None:
    parser = argparse.ArgumentParser(description="Read state from a WLMouse device.")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "--pid", type=hex_int, default=0, help="receiver product id in hex, e.g. a874"
    )
    args = parser.parse_args()
    logging.basicConfig(
        format="%(message)s", level=logging.DEBUG if args.verbose else logging.WARNING
    )
    try:
        state = read_device(args.pid)
    except PollError as err:
        code, reason = err.args
        print(json.dumps({"error": code}))
        print(f"{parser.prog}: {reason}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(state))


if __name__ == "__main__":
    main()
