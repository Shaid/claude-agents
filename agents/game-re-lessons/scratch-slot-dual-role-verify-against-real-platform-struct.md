# The same small-data/scratch slot can hold unrelated data across different loads or functions — prove it, don't assume a candidate reader is safe

**When it bites:** a small-data/scratch register or global offset (SAS/C
`An`-relative, or equivalent) that's already documented as holding one
kind of pointer in one function shows up in a *different* function doing
field reads that don't obviously fit that same interpretation, and the
new function's arithmetic is only "plausible-looking," not yet checked
against a real, externally-documented struct layout — **or** a candidate
consumer of a known multi-writer scratch field looks right (the kind of
code you'd expect) but nothing yet proves *which* of the field's several
writers it follows at runtime.

This project's `hunter/docs/explore/Wings/data-structure.md` already
documents pervasive SAS/C scratch-slot reuse across unrelated locals in
different subroutines (multiple prior sessions independently hit this for
other offsets). A follow-up session found a fresh instance: the exact same
two A4-relative offsets held a `struct BitMap*` double-buffer pair in one
function (used as a destination for a full-bitmap blit and later read for
its `Planes[0..4]` array by a bitplane-pointer-cache setup routine) but
were read, in a completely unrelated and far more generically-shared
hunk0 dispatcher function, as if they pointed at a palette struct (a
10-word copy starting at `+8`, matching the project's *other*, unrelated
confirmed palette-struct layout). Both readings were self-consistent
plausible arithmetic in isolation — the ambiguity was only resolved by
checking the `struct BitMap`-shaped function's field reads against
AmigaOS's real, public struct definition **byte-for-byte**: offset `+0`/
`+2` combining into a `BLTSIZE`-shaped `(rows<<6)|(bytesPerRow>>1)` word,
`+5` compared against a per-plane loop bound (`Depth`), and `+8/+12/+16/
+20/+24` read as a 5-entry pointer array (`Planes[]`) then written
straight into the hardware blitter's pointer registers — an exact,
unmistakable match to the real struct, not just "arithmetic that could
plausibly be a palette or a bitmap."

**The general move:** when a struct-field-read pattern in disassembly
loosely resembles a known platform struct (any OS/hardware-documented
layout — Amiga `struct BitMap`/`struct RastPort`, PSX `TMD`/`POLY_*`,
etc.), don't stop at "the arithmetic is consistent with this idea" —
pull the real struct's public field offsets and check every read against
them exactly (including any derived hardware-register-shaped
constructions, which are a much stronger tell than a bare offset match).
This is what distinguishes a confirmed struct identity from a merely
plausible one, and it's also what surfaces scratch-slot reuse as a
*named, documented* case rather than a silent source of contradictory
claims about what one small-data offset "is."

**A second, no-external-struct-needed technique for the same trap: prove
reuse by finding the identical loader instruction shape repeated with a
different literal argument.** No public struct exists to check a generic
"pointer to whatever was last loaded" scratch field against — but a
resource *loader* almost always has its own repeatable instruction shape
(the same handful of calls in the same order, ending in a store to the
scratch field), and that shape is reusable evidence on its own. Confirmed
on Valkyrie Profile (PSX, `valkyrie`): a small UI-icon bundle's load
sequence in the field/menu overlay (`jal <open>` / `jal <fetch>` /
`jal <register>` / a **delay-slot** `sw a0,0x14(ctx)`) looked, at first
read, like a plausible dedicated storage slot for that one resource — a
nearby candidate "consumer" read even looked right (built a screen rect,
called a draw routine). Searching the same overlay file for the
*identical* five-instruction shape with a different literal TOC-slot
argument found it verbatim, loading the totally unrelated battle-system
code overlay into the *same* scratch field. That one match is enough to
prove the field is genuinely multiplexed across incompatible resource
kinds — at which point the candidate "consumer" has to be dropped
(nothing in a static pass proves which load it follows at runtime) rather
than reported as a false positive. Use whichever proof is available: an
external struct definition when the platform documents one, or a
same-shape-different-literal search of the loader's own file when it
doesn't — both settle the same question, "is this offset genuinely
serving more than one role," before you trust any reader of it.
