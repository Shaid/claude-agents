# A file never opened by literal name may be a save file, not an asset

**When it bites:** string-searching the executable for a data filename comes up completely empty, even though the file clearly exists and is loaded somehow; or a container/disk-image directory listing shows a cluster of files with a much later modification timestamp than the rest.

Check whether the load path instead **enumerates a directory**
(`Lock`+`Examine`+`ExNext` or equivalent) via a file requester —
user-chosen filenames are never compile-time string literals, so a filename
search will never find them. This reframing cracked Frontier: Elite II's 5
"unknown compressed assets" as shipped savegames, ahead of any deeper
disassembly work.

**A second, cheaper detection signal: timestamp clustering in a directory
listing you already have.** When extracting a container/disk image that
preserves per-file timestamps (FAT12/GEMDOS, AmigaDOS, etc.), a subset of
files dated years later than the rest — especially ones matching an
original shipped filename rather than a distinct save-slot name — is the
signature of a played, in-place-saved disk/archive, not a pristine master.
The game persisted world/save state by overwriting same-named template
files rather than using separate save slots. Confirmed on a Phantasie II
(Atari ST) floppy dump: 24 of 47 files were dated 1995-10-06 against
1986-11/12 for the rest of that disk and the sibling disk — all 24 were
per-location `.DAT` files, a party/guild/inventory `.DAT`, and explicit
`.SAV`/`.BAC` files. Treat timestamp-outlier files as **live save state,
not guaranteed-canonical shipped data** when later decoding their internal
format — their content may reflect one specific playthrough.

**A timestamp cluster is a lead, not proof — two cheap follow-up checks turn
it into a decisive verdict once you have *any* already-confirmed sibling
format to check against.** Both confirmed on the same Phantasie II disk,
once its dungeon-file header/grid/action-table format was independently
decoded and verified:

1. **Byte-diff a suspected save file against its already-decoded pristine
   counterpart, once one exists.** `DNG.SAV` (1,024 B) and `DNGX.SAV`
   (2,500 B) share a filename stem with, and are close in size to, the
   confirmed-format `DNG1` (2,048 B, the level-0 dungeon). Diffing them
   byte-for-byte against `DNG1` found only 6 and 10 differing bytes
   respectively (out of ~2,048 compared) — i.e. `DNGX.SAV` **is** a
   snapshot of `DNG1` with a handful of live mutations, not independent
   content, and the trailing 452 bytes beyond `DNG1`'s length were plain
   zero padding. This only works once you have a confirmed decode of the
   sibling pristine format to diff against — but when you do, it's a much
   stronger and cheaper oracle than timestamp inspection alone, and the
   *specific* differing bytes are worth checking against the format's own
   documented runtime-mutation semantics: here, one 4-byte diff matched the
   dungeon engine's own documented "one-use action deactivation writes
   0x00" convention exactly, and five single-byte diffs all changed a
   fixed-encounter cell value to the same `0x8A` byte — a value a static
   reference-tool parser had labeled "never observed in real data,
   unassigned" purely because it only ever examined unplayed template
   files. The save-file diff retroactively supplied the missing runtime
   meaning (almost certainly "fixed encounter, already resolved") for a
   byte value the format doc had to leave as an open question. When a
   save/template pair diffs cleanly like this, treat every differing byte
   as free evidence about the *live* engine's write-back behavior, not just
   about save-vs-template status.
2. **A plain printable-ASCII-run scan over the suspect file is a decisive,
   near-zero-cost save-vs-template signal on its own, independent of
   timestamps.** `GUILD.DAT` (1995-dated) contains `PGLADE`, `PYOSHI`,
   `PKLEPTO` — a `P`-prefixed roster read straight off a plain string scan.
   Player-chosen names cannot appear in pristine shipped template data by
   definition; finding any of them settles the question immediately with
   no need for a sibling format or a byte-diff. Run this scan on every
   timestamp-outlier file before anything more elaborate — it's cheaper
   than either of the two techniques above and sometimes conclusive by
   itself.

**A third resolution for the same empty-filename-search symptom: the file is
a pristine *master copy* the engine never opens, because its sibling files
carry the live state and are written back in place.** Before concluding
"nothing reads this," check whether a *set* of related files is both loaded
and **saved** by the engine, and whether the silent file is a concatenation
or duplicate of their content (`oversized-file-may-be-concatenated-sibling-prefixes.md`
is the cheap test). Confirmed on Phantasie I (Amiga, `nicodemus` project):
`maps.int` appears nowhere in the 193 KB `game` executable's strings, which
initially read as "possibly not used by the shipped game at all." The engine
in fact builds `"OUT%-d.DAT"` with `sprintf` and calls a shared
open/read-**or-write**/close helper — the world map's fog-of-war flag is
written straight back into the per-section `out*.dat` files on every section
exit. `maps.int` is byte-identical to those files' concatenated grids
because it is the pristine master; the only executable naming it is a
separate `backup` disk utility that restores it. The diagnostic that
distinguishes this from the file-requester case: the missing filename's
content is *derivable from* other shipped files, and those siblings appear
in a save/write path, not only a load path. Note the knock-on for asset
extraction — files an engine saves in place are live save state, so a dump
taken from a played disk may not be canonical (this is the same hazard the
timestamp-clustering section above covers, reached from the opposite end).

Not every timestamp-outlier file resolves this cleanly: `TWNS.DAT`
(1995, 3,504 B) turned out to be a **structurally distinct, smaller**
save-state summary of the same town-name list held by the pristine
`TWNS.INT` (1986, 13,900 B) — not an overwritten copy of it, so the
pristine template file remained safely usable even though a same-content-
family save file existed alongside it. Don't assume every file in a
timestamp cluster resolves the same way; check each one.

**"Written by the game" is not "content is playthrough-specific" — residue
in a region the reader never touches classifies nothing.** A file the engine
demonstrably saves in place can still hold a completely pristine payload,
because save-write residue collects in whatever part of a fixed-size record
the format doesn't use. Confirmed on the same Phantasie II disk, correcting
an earlier verdict of this project's own: `OUT*.DAT` was closed as
"**confirmed save-mutated, not pristine content** — there is no known
pristine P2 counterpart", on three individually sound lines of evidence
(sparse gapped file numbering; ten files sharing a byte-identical block of
*unrelated* boilerplate text; `OUT1.DAT` embedding readable GEMDOS directory
entries for `DNG4`-`DNG8`, unmistakably a serialized open-file table). Every
one of those observations was real — and every one of them sits in the
995-1500 byte gap between the text block and the display list, which the
disassembled engine never reads back. Once the format was decoded, the
regions the engine *does* read proved untouched, and the pristine master
(`MAPS.INT`, 17 × 520-byte terrain grids, byte-identical to all 17
`OUT*.DAT` prefixes) had been sitting on the other floppy the whole time —
missed because it was filed as a `TWNS.INT`-adjacent disk-1 file rather than
as `OUT*.DAT`'s sibling. The same pass had also inferred a *content* claim
from the numbering gaps ("only outposts a specific playthrough visited get
written"); the pristine master contains exactly the same seventeen sections,
so the gaps are unreachable map, not unvisited locations.

Two rules fall out, both cheap:

- **Scope residue to the region it's in.** Before letting stale bytes
  classify a whole file, find out which byte ranges the reader actually
  consumes. Residue outside them says the file gets *written*, nothing more.
  (`proven-residue-does-not-bound-region-start.md` is the within-region twin:
  residue doesn't bound where the dead part *begins*, either.)
- **"No pristine counterpart exists" needs a search, not an absence you
  happened to notice.** Check every disk/archive in the release, not just the
  one the file lives on, and check by *content* (does any other shipped file
  contain this one's bytes as a substring?) rather than by filename or folder
  adjacency — `oversized-file-may-be-concatenated-sibling-prefixes.md` is the
  one-line test, and it works in this direction too.
