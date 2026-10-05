# A file never opened by literal name may be a save file, not an asset

**When it bites:** a string search of the executable for a data filename comes up empty although the file exists and is clearly used; or a container/disk-image listing shows a cluster of files with much later timestamps than the rest; or you are about to classify a file as "save-mutated, not pristine".

A file the code never names may be (a) a **user-chosen save** loaded via a file requester that enumerates a directory (`Lock`/`Examine`/`ExNext`) — user filenames are never compile-time literals; (b) a **played-disk save** that overwrote a same-named template in place; or (c) a **pristine master** the engine never opens because sibling files carry the live state and are written back.

**Check / fix:**
- **Look for directory enumeration / file requesters** in the load path before deeper disassembly.
- **Timestamp clustering** in a listing that preserves dates (FAT12/GEMDOS, AmigaDOS) is a lead: files dated years later, matching shipped names, mean a played disk. Treat them as live state, possibly one playthrough's.
- **Printable-ASCII scan** of each outlier: player-chosen names (a roster) cannot be in pristine data — decisive at near-zero cost; do it first.
- **Byte-diff a suspect against its decoded pristine counterpart** once one exists; the few differing bytes are free evidence of the engine's runtime write-back semantics, not just save-vs-template status.
- **Master-copy test:** is the silent file's content derivable from siblings that appear in a *write* path (`sprintf("OUT%-d.DAT")` + shared open/read-or-write helper)? Use `oversized-file-may-be-concatenated-sibling-prefixes.md` — and check every disk in the release, by content, before declaring "no pristine counterpart exists".
- **Scope residue to the bytes the reader consumes.** Save-write residue in a region the engine never reads says the file gets *written*, nothing about its payload (`proven-residue-does-not-bound-region-start.md` is the within-region twin).
- Check each outlier individually; a same-family file may be a distinct, smaller summary rather than an overwritten copy.

**Canonical example:** Phantasie II (Atari ST, `nicodemus`): 24 of 47 files dated 1995-10-06 vs 1986-11/12 — per-location `.DAT`s, a party/guild `.DAT`, `.SAV`/`.BAC`. `GUILD.DAT`'s string scan showed `PGLADE`, `PYOSHI`, `PKLEPTO`. `DNGX.SAV` (2,500 B) differed from the decoded `DNG1` (2,048 B) in only 10 bytes plus zero padding: one 4-byte diff matched the documented "one-use action deactivation writes 0x00", five set encounter cells to `0x8A` — a value a reference parser had called "never observed" because it only read templates (likely "encounter resolved"). `TWNS.DAT` (3,504 B) was a distinct summary of `TWNS.INT` (13,900 B), not a copy.

**Variants:**
- *File requester* — Frontier: Elite II's 5 "unknown compressed assets" were shipped savegames.
- *Pristine master* — Phantasie I (Amiga): `maps.int` is unnamed in the 193 KB `game`; the engine writes fog-of-war back into `out*.dat`; `maps.int` equals their concatenated grids and is named only by a `backup` utility.
- *Residue misclassification* — Phantasie II `OUT*.DAT` was closed as "confirmed save-mutated, no pristine counterpart" from gapped numbering, shared boilerplate, and embedded GEMDOS directory entries — all in the 995–1500 byte gap the engine never reads. `MAPS.INT` (17 × 520-byte grids, identical to all 17 prefixes) was on the other floppy; the numbering gaps were unreachable map, not unvisited places.

**History:** 4 recorded instances (Frontier, Phantasie I/II) — full log in `_archive/save-file-not-asset.md`.
