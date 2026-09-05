#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
SIMH_DIR=${SIMH_DIR:-"$ROOT/work/simh-v3.12-3"}
REPOSITORY=https://github.com/Computer-History-and-Simulation-Group/SIMH-v3.12-3.git
REVISION=d00ded27251550201560ec213867619610e56552

mkdir -p "$ROOT/work"
if test ! -d "$SIMH_DIR/.git"; then
    git clone "$REPOSITORY" "$SIMH_DIR"
fi
git -C "$SIMH_DIR" fetch origin "$REVISION"
git -C "$SIMH_DIR" checkout --detach "$REVISION"
make -C "$SIMH_DIR" vax780 TESTS=0
test -x "$SIMH_DIR/BIN/vax780"
printf '%s\n' "$SIMH_DIR/BIN/vax780"

