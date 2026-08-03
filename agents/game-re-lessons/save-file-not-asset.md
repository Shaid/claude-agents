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

Not every timestamp-outlier file resolves this cleanly: `TWNS.DAT`
(1995, 3,504 B) turned out to be a **structurally distinct, smaller**
save-state summary of the same town-name list held by the pristine
`TWNS.INT` (1986, 13,900 B) — not an overwritten copy of it, so the
pristine template file remained safely usable even though a same-content-
family save file existed alongside it. And some outlier files (P2's
`OUT*.DAT`) resisted both techniques above (no sibling pristine format to
diff against, no player-specific strings found) and stayed genuinely
inconclusive on content alone — timestamp remained the only evidence for
those. Don't assume every file in a timestamp cluster resolves the same
way; check each one.
