#!/usr/bin/env python3
"""Repair the NUL-corrupted turbulence row in the 1998 BRL-CAD snapshot."""

from __future__ import annotations

import argparse
from pathlib import Path


START = b"\t  {-0.299386323429644110"
END = b"\n\n\t  { 0.149970725178718570"
REPLACEMENT = b"""\t  {-0.299386323429644110,  0.432286161929368970,  0.484158257488161330, -0.180591955780982970,
\t   -0.471683348063379530,  0.256541807204484940, -0.160706320777535440,  0.273074500262737270,
\t    0.443456499371677640, -0.255790608935058120, -0.009335475042462349, -0.479141823947429660,
\t   -0.254775068257004020, -0.468241036403924230,  0.069491242058575153,  0.023787757847458124},"""


def repair(data: bytes) -> bytes:
    start = data.find(START)
    end = data.find(END, start + 1)
    if start < 0 or end < 0:
        raise ValueError("canonical turbulence row was not found")
    row = data[start:end]
    if b"\0" not in row:
        if row == REPLACEMENT:
            return data
        raise ValueError("turbulence row is neither corrupted nor canonical")
    return data[:start] + REPLACEMENT + data[end:]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    original = args.path.read_bytes()
    repaired = repair(original)
    args.path.write_bytes(repaired)


if __name__ == "__main__":
    main()

