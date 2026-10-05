# A cached runtime memory image regression-checked at one PC checkpoint can be stale for code reached later

**When it bites:** A CPU-emulation harness's cached/committed flat memory
dump (a `.bin` snapshot of RAM after boot) was regression-verified byte-exact
only up to an early `STOP_PC` checkpoint, and you're about to disassemble or
byte-diff that same cached file for code/data reached much later at runtime
(deep into gameplay, after many more frames/cycles) — especially if the
resulting decode looks *plausible but subtly off* (a shifted entry point, a
call target that resolves to the wrong address, a field that "should" be a
pointer but isn't) rather than obviously garbage.

## What went wrong

Desert Strike's Amiga boot-emulation harness (`tools/desertstrike/emu/`)
produces `build/cache/desertstrike/amiga/disk1_02.bin`, a flat dump of
emulated RAM taken after boot. The file had been regression-checked against
a live run only up to an early checkpoint (`STOP_PC=0x1c84`, i.e. shortly
after the loader hands off to the game engine) — that check passing was
treated as blanket confirmation the cached file was a faithful stand-in for
"live RAM" from then on.

It wasn't. A live `DUMP_RANGE` capture taken deep into actual gameplay
(~480M emulated cycles in, well past mission init) diverged from the cached
file at 2,237 of 2,560 sampled bytes in one window — the code/data the
cached file held at that address was simply different from what the real,
continuously-running emulation held there by that point. Disassembling the
stale cached bytes for a routine believed reachable at that address gave a
plausible-looking but wrong decode: the entry point was shifted by roughly
0x30 bytes, and a call site read as `jsr $536.l` instead of the live
capture's real `jsr $c00536.l` — a coherent, well-formed instruction either
way, so nothing about the stale decode looked broken on its own.

The plausible root causes (not chased further this session, since the fix
is procedural rather than diagnostic): later relocation, self-modifying
code, or bank/overlay-swapped content the boot-time snapshot simply hadn't
loaded yet. Any of these — and probably others — can make a "verified at
boot" cache diverge arbitrarily far downstream, with no signal in the file
itself that anything is wrong.

## The fix

A regression check at one checkpoint only proves the cache is valid *up to
that checkpoint*. For any address/routine believed reached only later in
execution, don't trust the cached file at face value — take a fresh live
capture (a `PC_HITS_LOG` register/return-address trace, or a targeted
`DUMP_RANGE` at the point of interest) and cross-check the cached file
against *that*, not just against the original boot-time regression target.
If they disagree, the live capture is authoritative; re-derive the decode
from it rather than patching around the stale cached bytes.

This generalizes past this one Musashi harness: any cheap-to-cache "golden"
memory/state snapshot for an emulated or interpreted target carries an
implicit "valid through cycle/instruction N" scope, even when nothing in its
filename or storage format records that scope explicitly.
