# A cracked/trainer loader can relocate a binary's whole file-I/O subsystem into a *different*, already-resident image

**When it bites:** a binary clearly must load more resources at runtime (the
game has dozens of asset files it obviously needs), but a byte-level OS-trap
census (GEMDOS/BIOS/XBIOS on Atari ST, `DOS_CALL`/`INT 21h` on DOS, library
`JSR -N(A6)` on Amiga) or a direct-hardware-register census across that
binary's own bytes comes back **completely empty** — no plausible call
setup anywhere, not even a handful of ambiguous hits.

## What went wrong

Hunter (Atari ST, `hunter` project): the real main executable (file `800`,
71,684 bytes) obviously needs to load a dozen-plus numbered resource files
(entity/save data, sound, pictures) at runtime. A byte-level census for
every GEMDOS `trap #1`, BIOS `trap #13`, XBIOS `trap #14`, and every direct
floppy-controller hardware register reference (`$FF8604`/`$FF8606`) across
the whole file found **zero legitimate call sites** — every opcode-byte
match lacked the canonical immediate-function-number push before it, i.e.
each was a coincidental data byte, not a real instruction. This looked like
strong, clean evidence the binary does its own I/O some other way entirely
(or not at all), and several plausible-but-wrong theories were chased first
(resident-loader callback address census, filename-string census, disk
sector-map reconstruction) — all also came back empty, because they were
still searching for evidence *inside the wrong file*.

The actual mechanism: the disk's small loader stub (`HUNTER.TOS`, 2,206
bytes) copies its **entire own TEXT segment** wholesale to a fixed resident
address early in its boot chain, before jumping into the main executable.
Once running, the main executable never calls a GEMDOS/BIOS/XBIOS trap
itself — the **cracker's patches redirect every load/save call site to a
`jmp` into that resident stub's address**, and the stub (well past its own
already-traced boot-chain `jmp` — the point a linear read of it would
naturally stop, since that jump is where *that* thread of execution ends)
contains a complete, hand-written FAT12-directory-walk-and-FDC-sector-read
file loader. The trap instructions are real and exist — just nowhere near
the file being censused.

## Fix

If a byte-level opcode/hardware-register census across an executable comes
back completely empty despite the binary obviously needing to do the thing
you're censusing for, don't conclude "this binary doesn't do X" — check
whether a **smaller loader/bootstrap binary earlier in the load chain copies
itself (or another module) to a fixed resident address** and keeps running
past the jump that ends *your already-traced* execution thread through it.
That "dead code past the boot jump" is not dead at all if the loaded binary
you're trying to understand can `jmp`/`jsr` an absolute address back into
it — read the rest of the loader stub's own bytes, not just the portion up
to the jump you already traced. This is a specific, high-value instance of
the general "read forward past a jump that only looks like an ending"
pattern in `confirmed-subroutine-does-not-bound-its-caller.md` and
`trace-stopped-at-staging-buffer.md`, but the boundary that gets missed here
is a **cross-binary** one (the loader stub, not the main executable's own
caller/callee structure), and it's specifically a signature of **cracked or
trainer-patched commercial disk images**, where "install N patches, most of
which are `jmp` targets into a relocated resident copy of the original
loader" is a common, deliberate crack pattern (bypassing copy-protection
checks in-place while keeping the original disk-format-aware I/O code
around, rather than reimplementing it). Confirmed this cost a full
`re-codebreaker` escalation to find on Hunter; the fix, once suspected, took
minutes (`Read`/disassemble `HUNTER.TOS`'s TEXT segment past its own
`jmp $800.w`).
