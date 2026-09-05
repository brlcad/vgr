# VAX-11/780 BRL-CAD VGR baseline

This workspace contains a reproducible SIMH VAX-11/780 environment for
recovering BRL-CAD's historical VGR baseline and assigning the missing
VAX-normalized reference to `sphflake`.

The working guest is 4.3BSD-Reno with 64 MB, a VAX FPA, GCC 1.42, and the
first BRL-CAD benchmark revision that contains `sphflake`. The launcher boots
the guest in single-user mode, optionally applies a SIMH cycle throttle, runs
all six scenes, captures their canonical RTFM lines, and calculates the
official five-scene arithmetic-mean VGR.

## Historical reference

The five archived logs in the [BRL-CAD repository](https://github.com/BRL-CAD/brlcad/tree/main/bench/ref)
identify `vgr.brl.mil` as a DEC VAX-11/780 with FPA, 64 MB, 4.3BSD, and
BRL-CAD 3.26 compiled on 26 August 1991.

| scene | rays | seconds | reference RTFM |
|---|---:|---:|---:|
| moss | 343,042 | 2,503.79 | 137.01 |
| world | 438,449 | 6,538.36 | 67.06 |
| star | 312,052 | 5,565.04 | 56.07 |
| bldg391 | 341,875 | 6,407.16 | 53.36 |
| m35 | 654,979 | 9,264.91 | 70.69 |

The original `perf.sh` definition is retained exactly:

```text
VGR = mean(observed_scene_RTFM / vgr_reference_scene_RTFM)
```

This is an arithmetic mean over those five scenes, not a ratio of totals or a
geometric mean. The reference values and formula are machine-readable in
[`config/vgr-reference.json`](config/vgr-reference.json).

The first repository revision containing the six-scene run is
[`eaa6c89f` (31 December 1998)](https://github.com/BRL-CAD/brlcad/commit/eaa6c89f8dec21fb8d5505a7d3190f9b8fb69a84).
Its archived `sphflake` log is a two-processor 1998 run on another host, so it
cannot be used as the VAX reference.

## What is pinned

- [SIMH v3.12-3](https://github.com/Computer-History-and-Simulation-Group/SIMH-v3.12-3),
  revision `d00ded27251550201560ec213867619610e56552`. The modern
  [SIMH repository](https://github.com/simh/simh) is the upstream project, but
  its current VAX780 model produced an adapter machine check while booting this
  period guest during setup.
- [4.3BSD-Reno distribution media](https://www.tuhs.org/Archive/Distributions/UCB/4.3BSD-Reno/),
  mirrored by TUHS. Reno is used because it is period-correct for the 1991
  reference and provides the ANSI/POSIX userspace needed to compile the 1998
  `sphflake` benchmark. Stock 1986 4.3BSD cannot compile that tree.
- GCC 1.42 for Reno from the
  [SIMH-ready package archive](https://sourceforge.net/projects/bsd42/files/Package%20Tapes/4.3%20BSD%20RENO/).
- BRL-CAD revision `eaa6c89f8dec21fb8d5505a7d3190f9b8fb69a84`.

All downloaded media are checksum-verified by `scripts/fetch-sources.sh`.
The small source patch in `patches/` selects GCC, disables NFS layout, and
addresses Reno lex/header and transitional build-file compatibility. The
1998 snapshot also has a literal 64-byte NUL hole in one turbulence-table row;
`tools/repair_turb.py` restores that row from BRL-CAD's maintained copy. No
ray-tracing algorithms or benchmark geometry are changed.

## Run it

The prepared disk is `work/vgr-reno.dsk`. To open its console:

```sh
make shell
```

To reconstruct the simulator and media from their public sources:

```sh
make simh media
```

The Reno tape must be cross-staged from stock 4.3BSD. Full disk construction is
documented in [`docs/guest-install.md`](docs/guest-install.md) and follows the
[published Reno-on-SIMH procedure](https://gunkies.org/wiki/Installing_4.3_BSD_RENO_on_SIMH).

## Calibrate and benchmark

SIMH's `SET THROTTLE` rate is cycles per second. The runner starts a fresh
simulator process for every candidate because this SIMH generation only allows
the throttle to be enabled once per process. Every calibration run is the
original 512-by-512 workload. The runner rejects `VGR_RT_ARGS`, and the metric
analyzer rejects logs that do not report exactly 262,144 pixels per scene.

Run a full-size calibration at a known cycle rate:

```sh
VGR_THROTTLE=1M make benchmark
VGR_THROTTLE=1M make metrics
```

The metrics command recommends the next rate as:

```text
next_rate = measured_rate / measured_legacy_VGR
```

Repeat the complete 512-by-512 benchmark at the recommended rate until the
five-scene arithmetic mean is close to 1.0:

```sh
VGR_THROTTLE=<calibrated-rate> make benchmark
VGR_THROTTLE=<calibrated-rate> make metrics
```

No reduced-resolution result is valid for throttle selection: it changes the
ray population, traversal mix, cache behavior, and ratio of setup to shot work.
The five reference scenes total 30,279 seconds of VAX CPU time, so a full
verification at VGR 1.0 takes about 8.4 CPU hours, plus `sphflake` and guest
overhead. The run also checks each full-size image against its archived pixels.

For an already extracted set of guest logs:

```sh
python3 tools/vgr_metrics.py --logs path/to/logs --throttle 950K
```

## Sphflake normalization

At any candidate throttle, the inferred VAX `sphflake` reference is:

```text
sphflake_VAX_RTFM = observed_sphflake_RTFM / legacy_mean_VGR
```

Once the five-scene mean is 1.0 this is simply the observed `sphflake` RTFM.
That value becomes the denominator for future `sphflake` VGR comparisons. The
same baseline run is therefore 1.0 by construction. Per-scene VGR spread is
reported alongside the mean; a single scalar throttle can match the official
mean exactly, but it cannot force five different instruction mixes to each be
exactly 1.0.

Run the host-side tests with `make test`.

## Measured full-frame calibration

On 28 August 2026, a complete six-scene run at 5,000,000 SIMH cycles per
second produced 262,144 pixels for every scene. `moss`, `world`, `star`,
`bldg391`, and `sphflake` matched all 786,432 archived output bytes; `m35`
had three bytes off by one and no bytes off by more, which the historical
comparator accepts.

The five legacy scenes measured a mean of `10.833618 VGR`, deriving a
verification throttle of `461526` cycles per second. SIMH v3.12-3 accepts only
integer values with a scale suffix, so the executable setting is `462K`; this
rounding predicts `1.0010 VGR`. The complete inputs and
results are recorded in [`config/calibration-5M.json`](config/calibration-5M.json).
Run the direct full-size verification with:

```sh
make benchmark-calibrated
make metrics-calibrated
```

The accelerated pass projects `sphflake` at about 64.35 RTFM, but that is not
the accepted baseline. The accepted value is the direct 512-by-512 sphflake
rate from the calibrated verification run.
