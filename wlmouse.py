import logging
import time
from contextlib import closing

import hid

VENDOR_ID = 0x36A7
REPORT_ID = 0
REPORT_LEN = 64
LENGTH = 3
COMMAND = slice(4, 6)
PAYLOAD = slice(6, REPORT_LEN)
REPLY_MARKER = 0xA1
RETRY_DELAY = 0.05
MAX_TRIES = 3

HEADERS = {
    "battery": "00 00 02 02 00 83",
    "profile": "00 00 02 02 00 85",
    "dpi": "00 00 02 02 01 82",
    "dpi map": "00 00 02 0a 01 81",
    "polling rate": "00 00 02 02 01 80",
}

log = logging.getLogger(__name__)


def interface_paths(product: int) -> list[bytes]:
    return list(dict.fromkeys(d["path"] for d in hid.enumerate(VENDOR_ID, product)))


def open_device(path: bytes) -> closing:
    dev = hid.device()
    dev.open_path(path)
    return closing(dev)


def read_report(dev) -> bytes:
    raw = bytes(dev.get_feature_report(REPORT_ID, REPORT_LEN + 1))
    # Some hidapi backends prefix the reply with the report id
    if len(raw) == REPORT_LEN + 1:
        raw = raw[1:]
    return raw.ljust(REPORT_LEN, b"\x00")


def hexdump(frame: bytes) -> str:
    return " ".join(f"{b:02x}" for b in frame[: PAYLOAD.start + frame[LENGTH]])


def is_reply_to(request: bytes, reply: bytes) -> bool:
    return reply[0] == REPLY_MARKER and reply[COMMAND] == request[COMMAND]


def query(dev, name: str, *payload: int) -> bytes | None:
    header = bytes.fromhex(HEADERS[name])
    assert len(header) == PAYLOAD.start, f"{name} header must be {PAYLOAD.start} bytes"
    request = (header + bytes(payload)).ljust(REPORT_LEN, b"\x00")
    for attempt in range(1, MAX_TRIES + 1):
        dev.send_feature_report(bytes([REPORT_ID]) + request)
        time.sleep(RETRY_DELAY * attempt)
        reply = read_report(dev)
        log.debug("%s > %s", name, hexdump(request))
        log.debug("%s < %s", name, hexdump(reply))
        if is_reply_to(request, reply):
            return reply[PAYLOAD]
    log.debug("%s ignored", name)
    return None
