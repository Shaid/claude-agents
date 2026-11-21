# A disk catalog mapped with the wrong unit still produces plausible-looking files

**When it bites:** you've turned a custom trackloader/boot catalog's block numbers into disk offsets (e.g. `block x 512` from disk 0) and accepted the mapping because the bytes at each computed offset "look like content" — 68k code, English text, pointer-shaped words — or a file's content seems to run seamlessly past its catalog entry's end.

On a dense disk almost any offset lands on something structured, so "sensible content at first and last block" cannot fail (see `check-that-cannot-fail-is-not-evidence.md`). A wrong unit or a missing reserved-prefix origin shifts every file by a different amount, so files start mid-neighbour, content "crosses" catalog boundaries with no transition, and a large share of the disk looks "uncatalogued". Those symptoms are evidence *against* the mapping, not discoveries about the data.

**Check / fix:**
- **No overlap:** no catalogued file may overlap the boot block, the loader, or the catalog's own sectors.
- **Exact ends:** a hunk executable must end exactly on its `HUNK_END`; a file with a length prefix must match the catalog size. Run the same check against the neighbouring entry as a null.
- **Coverage:** whole-disk accounting under the mapping should leave only fill bytes.
- **Read the loader's own sector maths** (e.g. `divu #11` then `+1 track`, or a WHDLoad slave's replacement routine) rather than assuming 512-B sectors from block 0.
- **Recognise CP/M:** 32-byte entries, `0xE5` as empty marker *and* fill byte, 8.3 name, extent byte, an RC count of 128-B records and 8 x u16 block pointers = a CP/M 2.2 directory, even on an Amiga trackloader disk. Allocation blocks are then typically 1-2 KB from the directory's own start.

**Canonical example:** Zeewolf 1 (Amiga, `hunter`, `docs/explore/Zeewolf/data-structure.md` §A1-A2): mapped as `block x 512` for months. That put `STARTUP.68K` at `0x800`, inside the stage-2 loader and the catalog, and produced a "headerless executable", a "mission-text database starting inside `TITLE.MOD` and running past the catalog's end", a pointer-census record grammar and "64% uncatalogued". The real mapping is 2 KB CP/M allocation blocks from track 1, `offset = 0x1600 + block x 2048`: STARTUP becomes a normal 5-hunk exe, `TITLE.MOD` a The Player 4.1A module, and every byte of the disk is accounted for.

**Variants:**
- Zeewolf 2 (same boot block and filesystem): length prefixes matched catalog sizes 35/35 under the right mapping vs 0/35 against the neighbour-entry null.

**Related:** `logical-offset-excludes-reserved-region.md` (reserved prefix shifts offsets), `self-consistent-chain-wrong-unit.md` (running sums pass in any unit).

**History:** 1 project (hunter, Zeewolf 1/2). Supersedes the retired `bootstrap-catalog-boundary-not-content-boundary` lesson, whose only example was this mis-mapping — its text is archived in `_archive/disk-catalog-wrong-unit-still-yields-plausible-files.md`.
