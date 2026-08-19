# The same small-data scratch slot can hold two unrelated struct types in two different functions — verify a suspicious field read against the real platform struct layout, byte-for-byte

**When it bites:** a small-data/scratch register offset (SAS/C `An`-
relative, or equivalent) that's already documented as holding one kind of
pointer in one function shows up in a *different* function doing field
reads that don't obviously fit that same interpretation — especially when
the new function's arithmetic is only "plausible-looking," not yet checked
against a real, externally-documented struct layout.

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
