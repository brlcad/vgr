#!/usr/bin/env python3
"""Calculate the historical VGR metric and a VAX sphflake baseline."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SCENE_ORDER = ("moss", "world", "star", "bldg391", "m35", "sphflake")
REQUIRED_PIXELS = 512 * 512
PIXELS_RE = re.compile(
    r"Frame\s+\d+:\s+(?P<pixels>\d+)\s+pixels\s+in\s+"
    r"(?P<seconds>[0-9.]+)\s+sec"
)
RTFM_RE = re.compile(
    r"Frame\s+\d+:\s+(?P<rays>\d+)\s+rays\s+in\s+"
    r"(?P<seconds>[0-9.]+)\s+sec\s+=\s+"
    r"(?P<rtfm>[0-9.]+)\s+rays/sec\s+\(RTFM\)"
)
CAPTURE_RE = re.compile(
    r"VGR-BEGIN\s+(?P<scene>[a-z0-9]+)\s*\n"
    r"(?P<body>.*?)"
    r"VGR-END\s+(?P=scene)",
    re.DOTALL,
)
HOST_RE = re.compile(r"\b[^@\s]+@(?P<host>[A-Za-z0-9.-]+):")


def parse_rtfm(text: str, source: str) -> dict[str, float | int | str]:
    normalized = text.replace("\r", "")
    pixel_matches = list(PIXELS_RE.finditer(normalized))
    if not pixel_matches:
        raise ValueError(f"no canonical pixel-count line in {source}")
    matches = list(RTFM_RE.finditer(normalized))
    if not matches:
        raise ValueError(f"no canonical RTFM line in {source}")
    values = matches[-1].groupdict()
    result = {
        "pixels": int(pixel_matches[-1].group("pixels")),
        "rays": int(values["rays"]),
        "seconds": float(values["seconds"]),
        "rtfm": float(values["rtfm"]),
    }
    host = HOST_RE.search(normalized)
    if host:
        result["host"] = host.group("host")
    return result


def read_log_directory(path: Path) -> dict[str, dict[str, float | int | str]]:
    observations = {}
    for scene in SCENE_ORDER:
        log = path / f"{scene}.log"
        if log.is_file():
            observations[scene] = parse_rtfm(log.read_text(errors="replace"), str(log))
    return observations


def read_capture(path: Path) -> dict[str, dict[str, float | int | str]]:
    text = path.read_text(errors="replace").replace("\r", "")
    observations = {}
    for match in CAPTURE_RE.finditer(text):
        scene = match.group("scene")
        if scene in SCENE_ORDER:
            observations[scene] = parse_rtfm(match.group("body"), f"{path}:{scene}")
    return observations


def parse_rate(value: str) -> float:
    match = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s*([kKmM]?)\s*", value)
    if not match:
        raise argparse.ArgumentTypeError("rate must look like 750K, 2.5M, or 1000000")
    multipliers = {"": 1.0, "k": 1_000.0, "m": 1_000_000.0}
    return float(match.group(1)) * multipliers[match.group(2).lower()]


def format_rate(rate: float) -> str:
    if rate >= 1_000_000:
        return f"{rate / 1_000_000:.6g}M"
    if rate >= 1_000:
        return f"{rate / 1_000:.6g}K"
    return f"{rate:.6g}"


def calculate(
    reference: dict,
    observations: dict[str, dict[str, float | int | str]],
    throttle: float | None,
) -> dict:
    legacy = reference["metric"]["legacy_scenes"]
    missing = [scene for scene in legacy if scene not in observations]
    if missing:
        raise ValueError("missing legacy logs: " + ", ".join(missing))

    wrong_size = [
        f"{scene}={row.get('pixels', 'missing')}"
        for scene, row in observations.items()
        if row.get("pixels") != REQUIRED_PIXELS
    ]
    if wrong_size:
        raise ValueError(
            "not a 512x512 benchmark (expected 262144 pixels; "
            + ", ".join(wrong_size)
            + ")"
        )

    hosts = {str(row["host"]) for row in observations.values() if "host" in row}
    if len(hosts) > 1:
        raise ValueError(
            "logs came from different hosts ("
            + ", ".join(sorted(hosts))
            + "); sphflake and legacy scenes must be one run"
        )

    rows = {}
    ratios = []
    for scene in legacy:
        observed = observations[scene]
        ref_rtfm = float(reference["scenes"][scene]["rtfm"])
        ratio = float(observed["rtfm"]) / ref_rtfm
        ratios.append(ratio)
        rows[scene] = {**observed, "reference_rtfm": ref_rtfm, "vgr": ratio}

    mean_vgr = sum(ratios) / len(ratios)
    scale_to_vax = 1.0 / mean_vgr
    result = {
        "legacy": rows,
        "legacy_vgr_arithmetic_mean": mean_vgr,
        "linear_scale_to_vgr_1": scale_to_vax,
        "legacy_vgr_min": min(ratios),
        "legacy_vgr_max": max(ratios),
    }

    if throttle is not None:
        result["measured_throttle_cycles_per_second"] = throttle
        result["suggested_throttle_cycles_per_second"] = throttle / mean_vgr

    if "sphflake" in observations:
        observed = observations["sphflake"]
        result["sphflake"] = {
            **observed,
            "projected_vax_reference_rtfm": float(observed["rtfm"]) * scale_to_vax,
            "method": "observed sphflake RTFM divided by the five-scene legacy VGR mean",
        }
    return result


def print_report(result: dict) -> None:
    print("scene       observed RTFM   reference RTFM       VGR")
    print("----------- -------------   --------------   -------")
    for scene, row in result["legacy"].items():
        print(
            f"{scene:11} {row['rtfm']:13.2f}   "
            f"{row['reference_rtfm']:14.2f}   {row['vgr']:7.4f}"
        )
    print()
    print(f"legacy arithmetic-mean VGR: {result['legacy_vgr_arithmetic_mean']:.6f}")
    print(
        "legacy scene range: "
        f"{result['legacy_vgr_min']:.4f} .. {result['legacy_vgr_max']:.4f}"
    )
    if "suggested_throttle_cycles_per_second" in result:
        rate = result["suggested_throttle_cycles_per_second"]
        print(f"next SIMH throttle estimate: {format_rate(rate)} cycles/sec")
    if "sphflake" in result:
        sph = result["sphflake"]
        print(f"projected VAX sphflake reference: {sph['projected_vax_reference_rtfm']:.2f} RTFM")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--logs", type=Path, help="directory containing SCENE.log files")
    source.add_argument("--capture", type=Path, help="console capture made by scripts/vax.exp")
    parser.add_argument(
        "--reference",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "config" / "vgr-reference.json",
    )
    parser.add_argument("--throttle", type=parse_rate, help="SIMH cycle rate used for this run")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    try:
        reference = json.loads(args.reference.read_text())
        observations = (
            read_log_directory(args.logs) if args.logs else read_capture(args.capture)
        )
        result = calculate(reference, observations, args.throttle)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"vgr_metrics: {error}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_report(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
