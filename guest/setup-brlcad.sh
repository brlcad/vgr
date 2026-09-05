#!/bin/sh
# Run as root in the Reno guest after the GCC and BRL-CAD tapes are attached.
set -e

BRLCAD_ROOT=/usr/brlcad
export BRLCAD_ROOT
PATH=/usr/brlcad/bin:/usr/local/bin:/bin:/usr/bin:/usr/ucb
export PATH

# GCC 1.42's bundled headers predate Reno's machtypes guard convention.
# Reno's own ANSI stddef/stdarg headers implement the VAX ABI correctly.
cd /usr/local/lib/gcc-include
test -f stddef.h.gcc || mv stddef.h stddef.h.gcc
test -f stdarg.h.gcc || mv stdarg.h stdarg.h.gcc

cd /usr/src/brlcad-4.6
mkdir -p /usr/brlcad
sh setup.sh <<EOF
yes
EOF
cake benchmark

