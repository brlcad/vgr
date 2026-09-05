#!/usr/bin/env python3
"""Decode the uuencoded boot42 block from the Gunkies raw wiki page."""

from __future__ import annotations

import argparse
import binascii
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    lines = args.source.read_text(errors="replace").splitlines()
    try:
        start = next(
            i
            for i, line in enumerate(lines)
            if line.startswith("begin ") and line.endswith(" boot42")
        )
    except StopIteration as error:
        raise SystemExit("boot42: no uuencoded block found") from error

    decoded = bytearray()
    for line in lines[start + 1 :]:
        if line == "end":
            break
        if line in ("", "`"):
            continue
        decoded.extend(binascii.a2b_uu(line.encode("ascii")))
    else:
        raise SystemExit("boot42: unterminated uuencoded block")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(decoded)


if __name__ == "__main__":
    main()
