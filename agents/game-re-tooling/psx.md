# Tooling — PSX (PlayStation 1)

`Read` this when working on a PSX target (a `.bin`/`.cue` raw CD dump, a
`PS-X EXE`). See `game-re-tooling/ps2.md` for the related but distinct PS2
conventions (different disc format, different addressing patterns), and
`game-re-tooling/ghidra-loaders.md` if you want Ghidra decompilation or PSYQ
symbol recovery rather than radare2's native `PS-X EXE` handling.

## Raw CD image sectors (MODE2/2352, CD-XA)

Redump-style `.bin`/`.cue` dumps store every sector as the full 2352-byte
raw frame, not the 2048-byte ISO9660 logical block:

```
0..11   sync pattern (00 FF×10 00)
12..14  address (min,sec,frame BCD)
15      mode (2 for Mode 2 / CD-XA)
16..19  subheader (file#, channel#, submode, coding_info)
20..23  subheader copy
24..    user data:
          Form 1 (submode & 0x20 == 0): 2048B data + 4 EDC + 172 ECC-P + 104 ECC-Q
          Form 2 (submode & 0x20 != 0): 2324B data + 4 EDC/spare (CD-XA streaming audio/video)
```

ISO9660 filesystem structures (PVD, directory extents) are **always**
Form 1 — safe to assume 2048B/sector when walking the filesystem tree.
Game data files can freely mix Form 1 and Form 2 per-sector (auto-detect
via the submode byte per sector, don't assume a whole file/extent is one
Form). A reference implementation (`PsxDiscImage` class: raw sector read,
Form1/Form2-aware logical read, PVD parse, directory walk) lives in
`~/Development/valkyrie/tools/shared/psx-cd.ts` — copy the pattern rather
than re-deriving it.

**Cheap sanity check that your Form1/Form2 bit and offset math is right**:
decode sector 16 (the PVD) as Form 1 and confirm the ISO9660 standard
identifier `CD001` appears at user-data offset 1 — if it doesn't, the
sync/header/subheader offsets or the submode bit are wrong, not the PVD
layout itself.

## PS-X EXE

Magic `"PS-X EXE"` (8 bytes ASCII) + a fixed 0x800-byte header (`pc0`,
`gp0`, `t_addr`/`t_size`, `s_addr` initial stack pointer, etc., all
little-endian `u32`s — see `~/Development/valkyrie/tools/valkyrieprofile/
vp-corpus.ts`'s `parsePsExeHeader` for exact offsets). **radare2
auto-detects this format natively with zero manual configuration** —
`open_file` alone gives `format: psxexe`, `arch: mips`, `bits: 32`,
`endian: little`; no `-a`/`-b`/`baddr` overrides needed the way raw/
headerless targets on other platforms often require.

PSY-Q SDK builds commonly leave debug `$Id: file.c,v ...` RCS-style
strings in `.rodata` even in retail, symbol-stripped binaries (`sys.c`,
`bios.c`, `intr.c` are typical) — useful for dating the SDK version, not
generally useful as game-specific data.

**Hand-rolled disassembly of a raw-extracted `PS-X EXE` needs `base =
t_addr − 0x800`, not `t_addr`.** If your own extraction helper (or one
that returns the *whole* file, header included, as `bytes`) hands you the
file's raw bytes rather than radare2's own auto-mapped view, that buffer's
byte 0 is the `"PS-X EXE"` magic — i.e. the start of the 0x800-byte
header — not the start of the text segment. Indexing into it with a
disassembler that assumes `image[addr - baseAddr]` and `baseAddr =
header.t_addr` silently desyncs the whole disassembly by exactly 0x800:
every instruction still decodes to *something* plausible-looking (valid
opcodes, no crash), but at the wrong address, so it won't match any
address a doc, a sibling verify script, or radare2 itself cites for the
same function. Confirmed on Valkyrie Profile (PSX, `valkyrie`): a
from-scratch probe using this project's own `extractMainExecutable` +
`disasmRange` with `base = exe.header.textAddr` produced a completely
different (but syntactically valid) function body at `0x800122c0` than an
already-passing sibling verify script using the same address with `base =
0x8000f800` (`= t_addr − 0x800`, hardcoded by that script for exactly this
reason). **Fix:** when reading a raw PS-EXE file buffer directly, subtract
0x800 from `t_addr` to get the address of file byte 0; radare2's own
`open_file`/`show_info` needs no such correction since it already
maps the segment for you.

**Once one script gets this wrong, the bug propagates by copy-paste.** A
project's verify scripts routinely clone an existing script's `IMAGES`/base
boilerplate to seed a new one, so a single wrong `base: 0x80010000` (the
`t_addr` literal, un-subtracted) tends to reappear verbatim in every sibling
script descended from it — confirmed on Valkyrie Profile: round 220 found
this exact wrong constant hardcoded in ~10 separate `verify-*.ts` files
across two rounds' worth of remediation. Don't stop at fixing the one
script a task flagged; `grep -rn '0x80010000' tools/<project>/` (or the
project's own equivalent literal) for the whole tree once you've confirmed
the bug in any single file, and fix every hit in the same pass.

## `CdlLOC`'s unused 4th byte can carry smuggled game data

The BIOS `CdlSetloc`/`CdControl` position struct (`CdlLOC`: minute/second/
frame BCD + a 4th byte nominally used for CD-DA track number) has its 4th
byte silently ignored by `CdControl(CdlSetloc, ...)` when seeking to a
Mode 2/Mode 1 data sector (track number only matters for audio tracks).
Confirmed on Valkyrie Profile (PSX): the game's on-disc resource directory
packs each entry as a raw `CdlLOC` word (for the seek) *plus* the high byte
of a 16-bit sector-count field stuffed into that unused 4th "track" byte —
effectively getting a free extra byte per directory entry by reusing a
BIOS-defined struct's dead field. When reverse-engineering any PSX
position/seek-related struct that's smaller than expected for the data it
must carry, check whether a field the BIOS call itself doesn't consume is
being reused for something else entirely — don't assume every byte in a
BIOS-shaped struct serves its nominal BIOS purpose.

## GTE control registers (`ctc2`/`cfc2`) as a free decode oracle

A `ctc2 $reg, $N` (or `cfc2`) instruction's control-register number `N` is
public, platform-wide, and doesn't vary per game — the same numbering every
PSX title's GTE coprocessor uses (`nocash`'s PSX-SPX and equivalent public
hardware docs). Recognizing that a scripted opcode/VM handler is loading a
scratch buffer into a specific `N` names what the buffer represents with no
further tracing needed — the same epistemic status as an SPU MMIO address
or a reset vector, not project-specific inference. Key groups worth
recognizing on sight: `cr0-4` rotation matrix, `cr5-7` translation vector,
`cr8-12` light-source matrix (LLM), `cr13-15` background colour (RBK/GBK/
BBK, ambient term), `cr16-20` **light-COLOR matrix** (LCM: LR1LR2/LR3LG1/
LG2LG3/LB1LB2/LB3 — consumed by `NCS`/`NCDS`/`NCCS` for per-vertex
directional-light colour tinting), `cr21-23` far colour, `cr24-25` screen
offset (OFX/OFY), `cr26` projection-plane distance (H), `cr27-28` depth-cue
interpolation (DQA/DQB), `cr31` FLAG. Confirmed on Valkyrie Profile (PSX,
`valkyrie`): a field-script opcode's own internal helper loaded 5 words via
`ctc2` into `cr16`-`cr20` — instantly identifying an otherwise-opaque
44-byte scratch region (open across 2 prior rounds as "purpose not
identified") as a scripted colored-lighting-tint (light-color-matrix)
setter, assembled one matrix row per opcode call. Cheaper than tracing the
buffer's own consumer chain when the consumer turns out to be fixed-function
hardware rather than more game code.

## Text encoding

PSX games developed in Japan (including US/EU SKUs of the same build) very
often carry Shift-JIS text somewhere, even in an English-localized retail
disc (leftover debug/internal strings, or an unremoved original-language
resource). Node's built-in `TextDecoder('shift_jis')` works out of the box
on a standard Node install — no `full-icu` build flag or extra package
needed (confirmed on real disc bytes, Node 22+). Don't reach for a
third-party Shift-JIS package before trying the built-in decoder first.
