#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
DOWNLOADS="$ROOT/work/downloads"
MEDIA="$ROOT/work/media"
BRLCAD_REPO="$ROOT/work/brlcad"
BRLCAD_STAGE="$ROOT/work/stage/brlcad-4.6"
BRLCAD_REV=eaa6c89f8dec21fb8d5505a7d3190f9b8fb69a84
RENO=https://okass.net/pub/mirror/minnie.tuhs.org/Distributions/UCB/4.3BSD-Reno
STOCK=https://okass.net/pub/mirror/minnie.tuhs.org/Distributions/UCB/4.3BSD
GCC_URL='https://sourceforge.net/projects/bsd42/files/Package%20Tapes/4.3%20BSD%20RENO/gcc-1.42.binary.BSD-4.3-RENO.tap.bz2/download'
BOOT_URL='https://gunkies.org/w/index.php?title=Boot42&action=raw'

mkdir -p "$DOWNLOADS" "$MEDIA" "$ROOT/work/stage"

fetch() {
    url=$1
    output=$2
    checksum=$3
    if test ! -f "$output"; then
        curl -L --fail --retry 3 -o "$output" "$url"
    fi
    printf '%s  %s\n' "$checksum" "$output" | shasum -a 256 -c -
}

fetch "$RENO/stand.gz" "$DOWNLOADS/stand.gz" e49ead51a57868ae022511333824d0fcea28c0aea9aac76ae0f3e45d216613a9
fetch "$RENO/miniroot.gz" "$DOWNLOADS/miniroot.gz" 1014a234a5ffd4074157eab1e72786df3c1c71ef6e707f04db898d0f6b0a4ffc
fetch "$RENO/rootdump.gz" "$DOWNLOADS/rootdump.gz" 39c3ccc33d75b957bac4ab08f1f50e0cb7f0a072b2689dfbb3b4f52c2721ea6e
fetch "$RENO/usr.tar.gz" "$DOWNLOADS/usr.tar.gz" 9be3cde8317b1d2a1106207d7a0fd2587ea2ae1f814fdd0a9bedbcd7d212b678
fetch "$RENO/srcsys.tar.gz" "$DOWNLOADS/srcsys.tar.gz" f0d3b86ab3e239a1861fee2b221a9f3f38b908c7931b9247a5d94584c9fd53f1
fetch "$GCC_URL" "$DOWNLOADS/gcc-1.42.tap.bz2" ce39242a89a267f122917927e6459d1202ea3a79f190f6c715ba525494c350fb
fetch "$STOCK/stand.gz" "$DOWNLOADS/stock-stand.gz" 8f5f38d1c141f598bf4fca16277960f463486f5d678e883a7de97af11ab148a2
fetch "$STOCK/miniroot.gz" "$DOWNLOADS/stock-miniroot.gz" 9f3c27b7ea99cec22b22a9eb8e25f85287087d031681476158e98b6ffffdebb5
fetch "$STOCK/rootdump.gz" "$DOWNLOADS/stock-rootdump.gz" 46d1ab1c41c330be47b04812f779c7e535b3e0d4d251b03670455660b212b125
fetch "$STOCK/usr.tar.gz" "$DOWNLOADS/stock-usr.tar.gz" 8565ff6f85ade24a1b63fdc5f7f5befe49b70bf4d44281cbfb015742ba379cc4

if test ! -f "$DOWNLOADS/boot42.raw"; then
    curl -L --fail --retry 3 -o "$DOWNLOADS/boot42.raw" "$BOOT_URL"
fi
python3 "$ROOT/tools/decode_boot42.py" "$DOWNLOADS/boot42.raw" "$MEDIA/boot42"
printf '%s  %s\n' a7bacc518350f4ebb1c21e7f578f91dd843ef42c26d912a1a9d227b2fac07eff "$MEDIA/boot42" | shasum -a 256 -c -

for name in stand miniroot rootdump usr.tar srcsys.tar; do
    gzip -dc "$DOWNLOADS/$name.gz" > "$MEDIA/$name"
done
for name in stand miniroot rootdump usr.tar; do
    gzip -dc "$DOWNLOADS/stock-$name.gz" > "$MEDIA/stock-$name"
done
bzip2 -dc "$DOWNLOADS/gcc-1.42.tap.bz2" > "$MEDIA/gcc-1.42.tap"

if test ! -d "$BRLCAD_REPO/.git"; then
    git clone https://github.com/BRL-CAD/brlcad.git "$BRLCAD_REPO"
fi
git -C "$BRLCAD_REPO" fetch origin "$BRLCAD_REV"

rm -rf "$BRLCAD_STAGE"
mkdir -p "$BRLCAD_STAGE"
git -C "$BRLCAD_REPO" archive "$BRLCAD_REV" \
    Cakefile Cakefile.defs setup.sh gen.sh sh cake cakeaux h bench pix db \
    libsysv libwdb libpkg libfb libbu libbn librt liboptical conv rt \
    libtcl/compat/strtod.c \
    | tar -xf - -C "$BRLCAD_STAGE"
# These two sources moved to libbn before the old librt Cakefile caught up.
cp "$BRLCAD_STAGE/libbn/font.c" "$BRLCAD_STAGE/librt/font.c"
cp "$BRLCAD_STAGE/libbn/sphmap.c" "$BRLCAD_STAGE/librt/sphmap.c"
cp "$BRLCAD_STAGE/libtcl/compat/strtod.c" "$BRLCAD_STAGE/libbu/strtod.c"
python3 "$ROOT/tools/repair_turb.py" "$BRLCAD_STAGE/liboptical/turb.c"
cp "$BRLCAD_STAGE/liboptical/turb.c" "$BRLCAD_STAGE/rt/turb.c"
patch -d "$BRLCAD_STAGE" -p1 < "$ROOT/patches/brlcad-4.6-vax-reno.patch"
cp "$ROOT/guest/setup-brlcad.sh" "$BRLCAD_STAGE/vgr-setup.sh"
chmod +x "$BRLCAD_STAGE/vgr-setup.sh"

tar -cf "$MEDIA/brlcad-4.6.tar" -C "$ROOT/work/stage" brlcad-4.6
python3 "$ROOT/tools/mktape.py" "$MEDIA/reno.tap" \
    "$MEDIA/stand:512" "$MEDIA/miniroot:10240" \
    "$MEDIA/rootdump:10240" "$MEDIA/usr.tar:10240"
python3 "$ROOT/tools/mktape.py" "$MEDIA/stock-43bsd.tap" \
    "$MEDIA/stock-stand:512" "$MEDIA/stock-miniroot:10240" \
    "$MEDIA/stock-rootdump:10240" "$MEDIA/stock-usr.tar:10240"
python3 "$ROOT/tools/mktape.py" "$MEDIA/srcsys.tap" "$MEDIA/srcsys.tar:10240"
python3 "$ROOT/tools/mktape.py" "$MEDIA/brlcad.tap" "$MEDIA/brlcad-4.6.tar:10240"
tar -cf "$MEDIA/vgr-config.tar" -C "$ROOT/config" VGR780
python3 "$ROOT/tools/mktape.py" "$MEDIA/vgr-config.tap" "$MEDIA/vgr-config.tar:10240"

printf 'Media written to %s\n' "$MEDIA"
