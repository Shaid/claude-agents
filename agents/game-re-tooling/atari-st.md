# Atari ST tooling

## `.STX` (Pasti) floppy disk images

`.STX` is the container format produced by the Pasti imaging tools (used by
the Steem SSE emulator) to preserve Atari ST floppies byte-for-byte,
including copy-protection artifacts (fuzzy/weak bits, non-standard sector
counts, embedded track images). Magic: `"RSY\0"` at offset 0.

**Spec source:** the format was never officially published by its author
(Ijor); the reverse-engineered write-up that actually has the byte-level
struct layout is "Pasti File Documentation" by Jean Louis-Guérin/DrCoolZic
(v0.5, Jan 2014): `http://info-coach.fr/atari/documents/_mydoc/Pasti-documentation.pdf`.
Fetch it with `WebFetch` then `Read` the saved PDF with the `pages` param —
`WebFetch`'s own HTML-conversion pass reported "encoded binary data, no
useful content" for this PDF, but `Read` extracts it fine. A web summary
page (e.g. atari.8bitchip.info) gets the broad shape right but not exact
enough to write a working parser first try; use the PDF as the source of
truth for field offsets/sizes.

**Structure:** File Descriptor (16 B: magic, version, tool, trackCount,
revision) → `trackCount` Track records. Each Track record: a 16 B Track
Descriptor (`recordSize` — add to this record's own start offset to get the
next Track Descriptor's offset; `fuzzyCount`; `sectorCount`; `trackFlags`
bit 0 = sector descriptors present, bit 6 = embedded track image present,
bit 7 = side, in `trackNumber`'s top bit not `trackFlags`; `trackLength`;
`trackNumber` = `(side<<7)|track`); then, if `trackFlags & 1`, `sectorCount`
16 B Sector Descriptors (`dataOffset` — relative to the start of the Track
Data region, i.e. *after* the sector descriptors and fuzzy mask, not
relative to the track descriptor; a 6 B copy of the address-block `id`
giving true track/head/sector-number/size/crc; `fdcFlags` — bit 7 fuzzy,
bit 4 RNF/no-data, bit 3 CRC error); then optional fuzzy-mask bytes; then
the Track Data region itself (optional Track Image header+content, plus
Sector Images for any sector whose bytes didn't match the Track Image
verbatim — this is a compression optimization, not extra data). Sector
byte size = `128 << (id.size & 3)`.

**Don't trust STX record order for physical layout.** Track records in the
file are not guaranteed to appear in side/track physical order (side A
tracks may not all precede side B, and imaging tools sometimes emit stub
records past the formatted area, e.g. tracks 80/81 with `sectorCount == 0`
on an 80-track disk). Group sectors by the `(side, trackNumber & 0x7F)`
pulled from each Track Descriptor, not by file position, when
reconstructing a flat image — a track-index-by-file-order approach will
silently scramble the image if any stub or reordered tracks are present.

**Extraction technique — don't write a full STX+FAT12 reader.** If the
target platform's filesystem is a variant your environment already has
tooling for (GEMDOS floppies are plain FAT12 — `mtools` reads them
natively), write only the narrow container→raw-image desectorizer (STX
sector/track descriptors → a flat, standard track-major/head-minor/
sector-minor byte stream) and hand the result to the existing filesystem
tool. This is far less code than reimplementing FAT12 directory/cluster
walking, and reuses a filesystem implementation that's already
battle-tested against edge cases you'd otherwise have to rediscover.
Confirmed on Phantasie II (Atari ST): a ~150-line Python desectorizer plus
stock `mtools` fully extracted two commercial floppy images, cross-verified
against the recovered `PHANT.PRG`'s `0x60 0x1A` GEMDOS executable magic
(the `bra.s`-opcode-as-program-header-signature convention — an external,
un-fakeable byte-exact oracle with no dependency on the STX/FAT12 parsing
being merely "close enough").

**`mtools` gotcha:** `mcopy`/`mdir` refuse a structurally perfect Atari ST
GEMDOS image with `Bad media types f7/f8, probably non-MSDOS disk` — the
`0xF8` media-descriptor byte is completely standard for double-density
floppies (Atari ST included) but mtools' sanity check expects PC-DOS
branding. Fix: `export MTOOLS_SKIP_CHECK=1` before invoking `mtools`
commands. This env var does **not** persist across separate tool-call
shells in an agent harness where each Bash invocation starts a fresh
shell — re-export it every call, or the symptom (an empty output directory,
`Cannot initialize '::'` on stderr, no other error) looks like a totally
different problem than a missing env var.

**Verifying a desectorized image without an emulator:** cross-check the
boot sector's BPB fields against the image you built (`total_sectors *
bytes_per_sector` must equal the raw image's byte length; the BPB's `heads`
field should match the side count you independently derived from the STX
track records — two unrelated sources of the same fact agreeing is real
evidence, not coincidence). Then confirm `mdir`'s reported total byte count
for the directory matches the actual extracted-file byte total exactly. If
any known executable is present, its header magic (GEMDOS/TOS `.PRG`:
`0x60 0x1A`) is a strong, free, format-specific oracle — check it before
trusting anything else.

## Disassembling GEMDOS/TOS `.PRG` executables (Capstone, not IRA/HUNK tooling)

A `.PRG` is **not** an Amiga HUNK executable — none of this project family's
HUNK-specific tooling (`amiga.md`, `HUNK_RELOC32` operand resolution, IRA)
applies. Structure: 28-byte header (`>HIIIIIIH`: magic `0x601A`, `text_len`,
`data_len`, `bss_len`, `symtab_len`, `reserved`, `prgflags`, `absflag`),
then `text_len` bytes of code, then `data_len` bytes of initialized data —
**contiguous in one flat, zero-based address space**: address `0` is the
first text byte, and data starts at address `text_len` (not a separate
segment with its own base). `file_offset = 28 + address` holds uniformly
across text *and* data — confirmed by finding literal immediate operands
(e.g. `move.l #$19f,d0`) that resolve to file offsets matching independently
grepped string locations exactly, on both Phantasie II's `START.PRG` (2,567
bytes, disassembles whole in one pass) and `PHANT.PRG` (155,785 bytes).
`bss_len` follows immediately after data in address space
(`[text_len+data_len, text_len+data_len+bss_len)`) but has **no file
bytes at all** — a `Setpalette`/similar call whose operand resolves into
this range is loading a *runtime-constructed* value, not something
readable statically from the file (confirmed: Phantasie II's `CROWD.PIC`
load target address fell in BSS, correctly flagging it as staged into a
working buffer rather than blitted straight from disk to screen).

Disassemble with Capstone from Python (no local m68k-aware disassembler
was needed): `capstone.Cs(capstone.CS_ARCH_M68K, capstone.CS_MODE_BIG_ENDIAN
| capstone.CS_MODE_M68K_000)`, fed the raw text-segment bytes starting at
address 0.

Two practical notes from re-using this on a second, unrelated subsystem of
the same `PHANT.PRG` (world-map loading, file I/O and movement dispatch, a
pass after the `.PIC` graphics work above): the `file_offset = 28 + address`
identity and the trampoline caveat below both held with zero friction, so
treat this technique as proven for general code tracing, not just for
locating graphics calls. But **Capstone silently emits nothing for a range
that starts mid-instruction** — `md.disasm()` returns an empty iterator
rather than an error, which reads exactly like "this range is data." Wrap it
in a loop that, on an empty result, prints the two bytes as `DC.W` and
advances by 2; that recovers sync automatically and makes real inline data
(jump tables, embedded filename strings between functions) visible instead
of invisible. Do not name your disassembly helper script `dis.py` — Python's
stdlib `dis` is imported by `inspect`, which Capstone imports, and the name
collision produces a confusing partially-initialized-module traceback.

**Finding OS/hardware calls (XBIOS `trap #$e`, GEMDOS `trap #$1`) needs a
two-hop search, not a single opcode scan, once the binary is large enough
to route calls through a shared wrapper.** A small loader may call a trap
directly inline (`move.w #$6,-(a7); trap #$e` — Setpalette, function 6;
byte-searchable as the literal 6-byte pattern `3F 3C 00 06 4E 4E`). A
larger executable instead routes *every* GEMDOS/XBIOS call through one
generic trampoline per trap vector (pops the pushed function number and
re-issues the trap at runtime) — so a direct `trap #$e` pattern search
finds only the trampolines themselves (as few as a literal handful across
a 150 KB binary: 8 on `PHANT.PRG`), not the real call sites. The fix:
(1) find the trampoline by locating the trap opcode itself and identifying
which one re-dispatches based on a stack argument rather than an inline
immediate; (2) find every caller of that trampoline via a raw `jsr
$target.l` byte-pattern search (`4E B9` + 4-byte big-endian target
address) over the whole text segment; (3) for each caller, disassemble a
short window immediately before it and check the preceding `move.w
#imm,-(a7)` for the pushed function number. Confirmed on `PHANT.PRG`: a
direct trap-opcode search found only 8 hits total (mostly unrelated
`Supexec` calls), while step (2) against the identified XBIOS trampoline
found 41 real call sites, 8 of them `Setpalette` (function 6) — invisible
to the single-pass search entirely.
