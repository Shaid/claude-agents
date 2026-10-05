# Amiga boot-block entry point is always struct offset 12 (`BB_ENTRY`), not 4

**When it bites:** starting to disassemble an Amiga boot-block's own 68000
code, and reaching for whatever file offset another game's doc (or your own
memory) claims is "the code start" instead of re-deriving it.

The real `struct BootBlock` (from `devices/bootblock.h`, and the RKM *Devices,
3rd ed.*'s own bootstrap description) is:

```c
struct BootBlock {
    UBYTE bb_id[4];       // offset 0: "DOS" + flags
    LONG  bb_chksum;      // offset 4: boot-block checksum (balance)
    LONG  bb_dosblock;    // offset 8: reserved for DOS patch
};                        // BB_ENTRY immediately follows, at offset 12 (0xC)
```

RKM *Devices, 3rd ed.*: "the address of the entry point for the boot code is
offset `BB_ENTRY` into the boot blocks in memory... invoked with the I/O
request... in register A1 [and] SysBase in A6." `BB_ENTRY = 12`. Bytes 4–7
are the checksum (data, not code, even though almost any 4 bytes will
*decode* as *some* nominally-valid 68k opcode — that's not evidence they're
executed); bytes 8–11 are reserved/unused by the ROM bootstrap for
non-filesystem boot blocks (a copy-protected disk is free to put anything
there, including a value that coincidentally looks like a plausible AmigaDOS
rootblock number).

**Confirmed independently on Millennium 2.2 (Amiga)**: file offset `0xC`
decodes as clean, semantically sound code (`movea.l #$66032,a3` — a
relocation-target load, part of a coherent self-relocating stub), while
offset `0x4` is measurably the checksum field. A sibling project's doc
(Deuteros, same repo family) describes its own boot block's code as starting
at offset 4 — that claim was **not** re-derived from the RKM in this session
and should not be assumed to generalize; it may be specific to that disk, or
may itself be worth re-checking. Every boot block's own bytes need this
five-second check (disassemble both offset 4 and offset 12, keep whichever
decodes as sensible code) — don't inherit another disk's claimed offset.

**Second confirmed instance, and the flagged Deuteros claim above was
checked and found wrong**: a later session re-derived Deuteros's own boot
block from scratch (`methanoid` project — Deuteros turned out to live in
the same repo as Millennium 2.2, not a separate `~/Development/deuteros`
as an even earlier pass's corpus note had assumed). Offset 4 decoded as
semantically nonsensical opcodes (`subi.b #2,d0` / `ori.b #0x70,d0` —
syntactically valid 68k, meaningless as a program start); offset `0xC`
decoded as clean, coherent code (`move.l a1,-(a7)` — pushing the RKM's own
documented A1-holds-the-ioreq boot-entry convention). The project's own doc
had to be corrected in place (it previously claimed offset 4 / RTS at
`0x92`; the real values are `0xC` / RTS at `0x9C`) — a second confirmed
case of exactly the mistake this file warns about, caught only because this
lesson file told the later session to re-derive rather than trust the
inherited claim.

**Fix:** before disassembling any Amiga boot block, confirm `BB_ENTRY=12`
against the RKM (`openground`'s `amigadocs` library, query "boot block
bootstrap code entry point checksum trackdisk" finds the exact struct
listing) or empirically (offset 12 decodes as sensible code; offset 4
doesn't). Don't copy an entry-offset claim from a sibling game's doc without
re-verifying it against this disk's own bytes.
