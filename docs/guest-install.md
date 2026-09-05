# Building the Reno guest disk

The checked-in launcher expects `work/vgr-reno.dsk`. A prepared disk may be
used directly; these are the reproducible construction notes. BSD distribution
files are downloaded rather than copied into this repository.

Reno's distribution tape is not independently bootable. It must be staged from
a working stock 4.3BSD guest, as documented by the contemporary SIMH procedure.

1. Run `make simh media`.
2. Install stock 4.3BSD on an RA81 disk using `work/media/stock-43bsd.tap` and
   `work/media/boot42`. The stock installation walkthrough is linked from the
   main README.
3. Make the stock disk `rq0`, a new RA81 disk `rq1`, attach `reno.tap` to `ts`,
   and boot stock 4.3BSD. In the stock guest, stage Reno on `ra1`:

       newfs /dev/ra1a ra81
       mkdir /mnt2
       mount /dev/ra1a /mnt2
       cd /mnt2
       mt -f /dev/rmt12 rew
       mt -f /dev/rmt12 fsf 2
       restore rf /dev/rmt12
       newfs /dev/ra1g ra81
       mkdir /mnt2/usr
       mount /dev/ra1g /mnt2/usr
       cd /mnt2/usr
       mt -f /dev/rmt12 rew
       mt -f /dev/rmt12 fsf 3
       tar xpbf 20 /dev/rmt12

4. Create `/mnt2/etc/fstab` with:

       /dev/ra0a / ufs rw 1 1
       /dev/ra0g /usr ufs rw 1 2

   Copy `/usr/mdec/*` into `/mnt2/mdec`, create empty `etc/sendmail.cf`,
   `etc/named.boot`, and `etc/exports`, then unmount `ra1g` and `ra1a`.
5. Stop SIMH, make the staged Reno disk `rq0`, and boot it with `boot42`. At
   the boot prompt enter `ra(0,0)vmunix`; answer `ra0` when the generic kernel
   asks for its root device. Mount `/usr` and run `MAKEDEV ts0` in `/dev`.
6. Attach `srcsys.tap`, rewind it, and extract it in `/usr/src/sys`. Attach
   `vgr-config.tap`, extract `VGR780`, and place it in `/usr/src/sys/conf`.
   Build and install the memory-sized kernel:

       cd /usr/src/sys/conf
       /usr/sbin/config VGR780
       cd ../VGR780
       make depend
       make
       cp /vmunix /vmunix.generic
       cp vmunix /vmunix
       sync

7. Stop SIMH, set the CPU to 64 MB, and reboot. The banner must say
   `real mem = 67108864` and identify `VAX 11/780`.
8. Attach `gcc-1.42.tap`; in the guest, rewind `/dev/rmt12`, change to `/`, and
   run `tar xpbf 20 /dev/rmt12`. Attach `brlcad.tap`, rewind, change to
   `/usr/src`, and extract it the same way. Finally run:

       sh /usr/src/brlcad-4.6/vgr-setup.sh

The last command installs Cake, builds the benchmark-only BRL-CAD 4.6 tree,
and leaves the runnable benchmark under `/usr/src/brlcad-4.6/vax/bench`.

Always issue `sync` before stopping the simulator or copying the disk image.
