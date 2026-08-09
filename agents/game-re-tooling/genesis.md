# Tooling — Sega Genesis / Mega Drive (68000+Z80, VDP, YM2612)

No RE work has been done on this platform under this account yet — this
file currently holds reference material only, filed here in advance so a
future Genesis/Mega Drive session doesn't have to re-locate it. Fetched
2026-08-02 after a comparison to `fullsnes.txt` (see `snes.md`).

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

No Genesis/68k Ghidra loader exists in any surveyed public collection — see
`game-re-tooling/ghidra-loaders.md` § Gaps.

No SpritesMind (`gendev.spritesmind.net`) content was fetched this pass —
that forum/doc hub is widely considered the actual community hub for
Genesis dev discussion and has its own documentation page
(`gendev.spritesmind.net/page-doc.html`), but wasn't pulled locally since
it's more of a forum archive than a single reference doc; revisit if a
real Genesis project starts and Kabuto's notes prove insufficient.

## When real RE work starts here

Once this account actually works a Genesis/Mega Drive corpus, replace/
extend this file with the same kind of concrete, corpus-tested technique
notes `snes.md`/`amiga.md`/`dos.md` have (sharp edges in whatever
disassembler gets used, census techniques that worked, gotchas specific
to the 68000+Z80 dual-CPU setup) — this version is deliberately just a
reference-material drop, not lessons learned.
