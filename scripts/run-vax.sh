#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
MODE=${1:-shell}
case "$MODE" in
    shell|calibrate|benchmark|collect) ;;
    *) echo "usage: $0 [shell|calibrate|benchmark|collect]" >&2; exit 2 ;;
esac

if test -n "${VGR_RT_ARGS:-}"; then
    echo "VGR_RT_ARGS is intentionally unsupported: VGR calibration must use the unmodified 512x512 benchmark" >&2
    exit 2
fi

SIMH_BIN=${SIMH_BIN:-"$ROOT/work/simh-v3.12-3/BIN/vax780"}
VGR_DISK=${VGR_DISK:-"$ROOT/work/vgr-reno.dsk"}
BOOT42=${BOOT42:-"$ROOT/work/media/boot42"}
THROTTLE=${VGR_THROTTLE:-}
RESULTS=${VGR_RESULTS:-"$ROOT/results"}

case "$THROTTLE" in
    ""|*[KkMm]) ;;
    *)
        echo "VGR_THROTTLE must include a K or M suffix (for example, 461.526K)" >&2
        exit 2
        ;;
esac

test -x "$SIMH_BIN" || { echo "missing simulator: $SIMH_BIN" >&2; exit 1; }
test -f "$VGR_DISK" || { echo "missing guest disk: $VGR_DISK" >&2; exit 1; }
test -f "$BOOT42" || { echo "missing boot loader: $BOOT42" >&2; exit 1; }
command -v expect >/dev/null || { echo "expect is required" >&2; exit 1; }

mkdir -p "$RESULTS"
INI=$(mktemp /tmp/vgr-simh.XXXXXX)
trap 'rm -f "$INI"' EXIT HUP INT TERM

{
    echo 'set cpu 64m'
    if test -n "$THROTTLE"; then
        echo "set throttle $THROTTLE"
        echo 'show throttle -d'
    fi
    echo 'set rq0 ra81'
    echo "attach rq0 $VGR_DISK"
    echo 'set rq1 disable'
    echo 'set rq2 disable'
    echo 'set rq3 disable'
    echo 'set rp disable'
    echo 'set lpt disable'
    echo 'set rl disable'
    echo 'set tq disable'
    echo 'set tu disable'
    echo "load $BOOT42 0"
    echo 'run 2'
} > "$INI"

export VGR_ROOT="$ROOT" VGR_SIMH_BIN="$SIMH_BIN" VGR_SIMH_INI="$INI"
export VGR_MODE="$MODE" VGR_RESULTS="$RESULTS"
exec expect "$ROOT/scripts/vax.exp"
