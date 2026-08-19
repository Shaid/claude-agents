# Tooling — Sega Genesis / Mega Drive (68000+Z80, VDP, YM2612)

The `strike` project (`game-re-corpora/strike.md`) has done substantial
real Genesis/Mega Drive RE work across several sessions (Desert/Jungle/
Urban Strike) — check that corpus file first for solved container/codec
formats before re-deriving anything from scratch. The reference-material
section below was filed in advance (2026-08-02, before that work started)
so a Genesis/Mega Drive session wouldn't have to re-locate it; the
technique note further down is corpus-tested.

## References (local copies in `genesis-reference/`)

Unlike SNES, there's no single-author, single-file equivalent of
`fullsnes.txt` for the Genesis/Mega Drive — the community-standard
reference is split across a couple of sources:

- **`genesis-reference/plutiedev-kabuto-hardware-notes.txt`** — the real
  register/timing-level reference, closest in spirit and depth to
  fullsnes.txt. Written by Kabuto (of TiTAN) during Overdrive 2's
  development; covers the bus system, YM2612, VDP ports, picture
  size/H+V counter values, sprite-rendering internals (phase-by-phase),
  and known hardware glitches/quirks. Mirrored via
  `https://plutiedev.com/mirror/kabuto-hardware-notes` (itself a mirror of
  a Google Docs original — check that URL if this copy goes stale).
- **`genesis-reference/exodus-hardware.txt`** — a catalog of official and
  third-party **development hardware** (Super Mega Drive/"Super Target",
  32X Development Target, ICE units, etc.) — historical/collector-level
  detail, not register specs. Useful for understanding what dev hardware
  existed, not for programming reference.
- **`genesis-reference/exodus-software.txt`** — community and original
  development tools, test ROMs.
- **`genesis-reference/exodus-documentation-index.txt`** — an index page
  linking out to **scanned original manuals** (the official "Genesis
  Software Manual", "Super Mega Drive Manual", etc.) hosted as external
  Google Drive PDFs — those PDFs were NOT downloaded (large binary scans,
  fetch on demand if a specific manual is actually needed; the links are
  preserved in this text file).
- **`genesis-reference/exodus-overview.txt`** — short overview/landing
  page, minimal content on its own.
- Source site for all `exodus-*.txt` files:
  `http://techdocs.exodusemulator.com/Console/SegaMegaDrive/` (four pages:
  `index.html`, `Hardware.html`, `Software.html`, `Documentation.html` —
  re-fetch from there if these copies go stale; the site covers other Sega
  systems too under sibling `/Console/`/`/Arcade/` paths, not mirrored
  here since they're out of scope).

## Not yet covered

A Genesis/68k Ghidra loader (`ghidra_sega_ldr`) is now installed — see
`game-re-tooling/ghidra-loaders.md`. It parses the headered `.bin`/`.md` ROM
container; the 68000 CPU support itself is stock Ghidra.

No SpritesMind (`gendev.spritesmind.net`) content was fetched this pass —
that forum/doc hub is widely considered the actual community hub for
Genesis dev discussion and has its own documentation page
(`gendev.spritesmind.net/page-doc.html`), but wasn't pulled locally since
it's more of a forum archive than a single reference doc; revisit if a
real Genesis project starts and Kabuto's notes prove insufficient.

## Hand-decoding a `JMP d16(PC,Dn.W)`-into-a-branch-array dispatch when a linear disassembler desyncs

A classic 68k space-saving jump-table idiom: instead of a table of raw
absolute addresses, the "table" is a physically contiguous run of real,
executable `BRA.W <disp>` instructions (4 bytes each: 2-byte opcode + 2-byte
displacement), and the dispatch computes an index that lands the `JMP` **2
bytes into** the target slot — i.e. exactly on that slot's own displacement
word, which the CPU then happily executes as if it were a fresh opcode
(word `0xNNNN` reinterpreted as whatever 2-byte instruction those bits
encode when the branch's *own* displacement value permits, or more commonly
the slot is laid out so index 0 lands cleanly on a real `BRA.W` opcode
boundary and each subsequent index is a further `BRA.W`-worth along). A
linear/interactive disassembler (confirmed: radare2) walking this region
top-to-bottom desyncs immediately, since it has no way to know which byte
the real execution path actually starts on for a given case — the resulting
listing shows garbage instructions or, worse, plausible-looking-but-wrong
ones for large stretches.

**Fix, confirmed on Urban Strike (Mega Drive)'s `cmd=18` graphics codec**
(`fcn.000077e0`, file offset `0x77e0`; see `game-re-corpora/strike.md`):
stop trusting the disassembler's linear walk of that region entirely and
hand-compute each case's real entry address directly from a hexdump. For
the 68k brief-extension-word addressing mode `JMP d(PC,Dn.W)` (opcode
`4EFB`, extension word e.g. `6000`): the effective address is
`extensionWordAddr + base8 + signExtend16(Dn)`, where `extensionWordAddr`
is the address of the extension word itself (2 bytes after the `JMP`
opcode) and `base8` is the extension word's own low byte (0 in the brief
format unless otherwise set). Once you have that formula, read each
candidate case's raw bytes directly: `6000 dddd` at a table slot is itself
just another `BRA.W`, whose *own* target = `(slotAddr+2) + dddd` — chase
that one more hop to find the real case body, then decode its opcodes by
hand from the hexdump (a handful of common 68k opcodes — `SWAP Dn`
(`0x4840`+n), `MOVE.W (An)+,Dn`, `MOVE.L (An)+,Dn`, `EXG` — cover most
"register refresh"-style dispatch bodies). This is faster and more
reliable than trying to coax a confused interactive disassembler into
re-syncing, and was how this session cracked a previously-unidentified
4th Mega Drive Strike-engine tile-compression codec from scratch by hand,
verified byte-exact against 129 real ROM instances afterward.

## When more RE work lands here

Extend this file with further concrete, corpus-tested technique notes
(more disassembler sharp edges, census techniques, 68000+Z80 dual-CPU
gotchas) as future Genesis/Mega Drive sessions turn them up.
