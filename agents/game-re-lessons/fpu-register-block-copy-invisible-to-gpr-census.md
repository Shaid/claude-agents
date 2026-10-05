# FPU-register block copies are invisible to a GPR-only load/store census on any MIPS target with an FPU

**When it bites:** a MIPS binary from a platform with a hardware FPU (PSP,
PS2, N64 — not PSX/PS1, which has no FPU) needs a byte-pattern census of
every load/store touching some address or struct field, the census already
includes the ordinary GPR opcodes (`lb`/`lh`/`lw`/`lbu`/`lhu`/`lwl`/`lwr`
and their store counterparts) plus `lwc2`/`swc2` (op `0x32`/`0x3a`, for the
GTE) "to be thorough," and it returns a clean negative for a consumer you
have independent reason to believe exists on that platform.

## The trap

`lwc1`/`swc1` (opcodes `0x31`/`0x39`) and `ldc1`/`sdc1` (`0x35`/`0x3d`) move
a 32- or 64-bit value between memory and a coprocessor-1 (FPU) register.
Nothing requires the moved bits to be a float — a compiler doing a fast
register-width `memcpy` of an opaque data block (an array of `int32`s, a
struct with no floating-point fields at all) is free to route it through
`$f` registers exactly like any other 32-bit move, and optimizing MIPS
compilers routinely do this for block copies because it frees up GPRs and
can pair better on some pipelines. The instruction encoding gives no hint
that the underlying data is non-float; only the *source* format (an array
of confirmed integers) tells you the FPU move is a plain copy, not real
floating-point arithmetic.

A census that enumerates "every load/store" but stops at the GPR opcode set
plus `lwc2`/`swc2` (added because the GTE is a well-known coprocessor-2
consumer on PSX/PS2) will silently skip every `lwc1`/`swc1`/`ldc1`/`sdc1`
site — not an error, not a crash, just zero matches where a real one
exists.

## Confirmed case

Valkyrie Profile: Lenneth (PSP remaster, `valkyrie` project). The PSX
original's battle party-formation initializer copies a 48-byte, three-table
stack block using plain `lw`/`sw`. The PSP port (`Battle_master.prx`, a
different compiler over the same source, not just a recompiled binary with
identical code) performs the byte-identical copy via a sequence of `lwc1
$fN,off($v0)` / `swc1 $fN,off($sp)` pairs — using the FPU purely as a
32-bit register file for the copy, with no floating-point semantics
involved at all (the source data is a plain `int32` array, independently
confirmed byte-identical to the PSX side). A first PSP-side consumer
census, built by carrying over the PSX-side opcode set (GPR ops +
`lwc2`/`swc2`) verbatim, found **zero** references to this block on the PSP
side, even though the PSX sibling function performing the identical copy
was already fully traced. Re-running the same census with `0x31`/`0x35`/
`0x39`/`0x3d` added found the copy immediately, and it turned out to be
essential corroborating evidence: the PSP port's independent compilation of
the same source confirmed a PSX-side finding (a mislabelled sibling-table
read, see `struct-field-scan-blind-to-biased-base-pointer.md`'s "sibling-
table variant") that a single-platform census alone could not have settled
as confidently.

## Fix

Any "every load/store" census over a MIPS image from an FPU-equipped
platform (PSP/PS2/N64; **not** needed for PSX/PS1, which has no FPU and
never emits these opcodes) must include the full coprocessor-1 move set —
`lwc1`/`swc1` (`0x31`/`0x39`) and `ldc1`/`sdc1` (`0x35`/`0x3d`) — alongside
the GPR opcodes and `lwc2`/`swc2`. Don't assume "this data isn't floating
point" rules out an FPU-register move; the compiler doesn't care what the
bits mean when it's just relocating them. This is the same lesson as
`narrow-opcode-form-census-false-negative.md` (an opcode-form coverage gap
in a consumer census) with a platform-specific trigger worth naming on its
own: it only bites when porting a census built against a PSX/PS1 sibling
straight over to a PSP/PS2/N64 target, since the PSX side of the same
project never needs this opcode class at all.
