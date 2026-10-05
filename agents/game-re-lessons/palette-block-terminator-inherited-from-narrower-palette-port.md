# A block-list terminator rule inherited from a narrower-palette port silently truncates the wider palette

**When it bites:** a `[start][count][entries]` palette (or any indexed
block list) reader on a 256-entry platform reuses a sibling platform's
sentinel test of the form `start >= 0x80` / `index >= N` — and several
files are being described as "no self-defined colours", "needs a donor",
or render black/wrong for exactly the indices above that threshold, while
the reader's own byte-exact region-closure check passes on a plausible
subset of files.

Dune (DOS VGA, `wyrm`): the DOS palette reader copied Amiga's block
terminator (`start >= 0x80`, correct there — a 32-colour palette never
has a real block at 128+). On VGA, blocks starting at 128-254 are the
*norm* for room-decoration banks (`por` 129-182/240-254, `siet1`
128-207/225-232/240-254, `bunk` 129-176, `mirror` 129-173, ...). The
game's own uploader (`DUNEPRG.EXE 0xc2a2`) stops only on the word
`0xFFFF`, treats `count == 0` as 256 and skips the `start=0,count=1`
placeholder. For weeks the truncation was misdiagnosed as a palette-donor
problem ("`siet1`/`por`/`mirror` have zero self-defined colours") and a
sietch room set rendered as black silhouettes; with the `0xFF` rule the
files are fully self-palettised and the donor question for one of them
disappeared entirely.

Why the closure check didn't catch it: "30 files close byte-exact on their
declared palette region" was true — for the subset whose blocks all
started below 128. The files that didn't close were filed as "tiny or
absent self-palette" rather than as the reader stopping early. A
truncating sentinel produces a *clean* partial parse, not an error.

**Fix:** a sentinel/terminator value is a property of the platform's
index width, not of the container family — re-derive it per port from the
loader (`cmp ax,0xffff`-shaped test) or from the widest block the corpus
actually declares, and require region closure on **every** file with a
non-empty palette region (55/55 here), treating each non-closing file as a
reader bug until shown otherwise. Sibling traps in the same family:
`platform-port-swaps-adjacent-header-fields.md` (field order) and
`sibling-format-shares-field-position-not-numeric-scale-convention.md`
(numeric scale) — this one is the *sentinel* axis.
