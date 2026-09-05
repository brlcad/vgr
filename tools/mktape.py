#!/usr/bin/env python3
"""Create a SIMH .tap image from file:block-size pairs.

Each argument after the output path is FILE:BLOCK_SIZE.  Input files are
split into fixed-size tape records, padded with NUL bytes, and separated by
SIMH tape marks.  The result is suitable for ATTACH TS in SIMH.
"""

from __future__ import annotations

import argparse
import struct
from pathlib import Path


def write_record(output, payload: bytes) -> None:
    output.write(struct.pack("<I", len(payload)))
    output.write(payload)
    if len(payload) & 1:
        output.write(b"\0")
    output.write(struct.pack("<I", len(payload)))


def add_file(output, path: Path, block_size: int) -> None:
    with path.open("rb") as source:
        while block := source.read(block_size):
            if len(block) < block_size:
                block += b"\0" * (block_size - len(block))
            write_record(output, block)
    output.write(struct.pack("<I", 0))


def parse_input(value: str) -> tuple[Path, int]:
    try:
        name, size = value.rsplit(":", 1)
        block_size = int(size)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            f"expected FILE:BLOCK_SIZE, got {value!r}"
        ) from error
    if block_size <= 0:
        raise argparse.ArgumentTypeError("block size must be positive")
    path = Path(name)
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"not a file: {path}")
    return path, block_size


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("inputs", nargs="+", type=parse_input)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("wb") as output:
        for path, block_size in args.inputs:
            add_file(output, path, block_size)
        output.write(struct.pack("<I", 0))


if __name__ == "__main__":
    main()
