#!/usr/bin/env python3
"""Load a board's custom token into its NVS over USB serial.

The token comes from `tools/seed_couple.py --mint-tokens` and is never printed.
Before sending, the script asks the board for its device ID (`status`) and
refuses if it does not match the token file, so a token cannot go to the wrong
board.

  python tools/provision_device.py --port COM6 --device-id hs-20500dcdfd18

Requires: pip install pyserial
"""
import argparse
import os
import re
import sys
import time

import serial


def read_until(port: serial.Serial, pattern: re.Pattern, timeout_s: float):
    end = time.time() + timeout_s
    buf = ""
    while time.time() < end:
        chunk = port.read(512).decode("utf-8", "replace")
        if chunk:
            buf += chunk
            match = pattern.search(buf)
            if match:
                return match, buf
    return None, buf


def main() -> int:
    parser = argparse.ArgumentParser(description="Provision a board's custom token over serial")
    parser.add_argument("--port", required=True)
    parser.add_argument("--device-id", required=True)
    parser.add_argument("--token-dir", default=os.path.join(os.path.dirname(__file__), ".device-tokens"))
    parser.add_argument("--baud", type=int, default=115200)
    args = parser.parse_args()

    path = os.path.join(args.token_dir, f"{args.device_id}.token")
    if not os.path.exists(path):
        print(f"no token file {path}: run tools/seed_couple.py --mint-tokens first")
        return 1
    with open(path, encoding="ascii") as f:
        token = f.read().strip()
    if len(token) + 7 > 2047:
        print("token too long for the board's serial line buffer")
        return 1

    # Open without toggling DTR/RTS, so the board is not reset.
    port = serial.Serial()
    port.port = args.port
    port.baudrate = args.baud
    port.timeout = 0.2
    port.dtr = False
    port.rts = False
    port.open()
    try:
        port.reset_input_buffer()
        port.write(b"status\n")
        match, _ = read_until(port, re.compile(r"id=(hs-[0-9a-f]{12})"), 5)
        if not match:
            print(f"{args.port}: no status reply (is the heartsync firmware running?)")
            return 1
        found = match.group(1)
        if found != args.device_id:
            print(f"{args.port} is {found}, not {args.device_id}: refusing to send the token")
            return 1
        port.write(f"token {token}\n".encode("ascii"))
        match, buf = read_until(port, re.compile(r"custom token stored|token rejected|line too long"), 5)
        if not match or match.group(0) != "custom token stored":
            print(f"{args.port}: board did not accept the token")
            return 1
        print(f"{args.port}: token stored on {found}; it will sign in once Wi-Fi is up")
        return 0
    finally:
        port.close()


if __name__ == "__main__":
    sys.exit(main())
