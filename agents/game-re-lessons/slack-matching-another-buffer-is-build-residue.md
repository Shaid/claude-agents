# Slack bytes that equal another buffer at the same relative offset are residue, not content

**When it bites:** a file or track has bytes past its real content: a "trailer", "two extra rows", "orphan" records, an "abandoned 8th instrument". You're about to model them, or file them as unfalsifiable.

Build tools and in-place decompressors leave predictable leftovers. A disk builder writes each file from a reused buffer, so the slack after a short file holds the previous, longer file at the **same relative offset**. An in-place decompressor that overshoots copies part of its own compressed **input** into the output tail. A sequel's data files authored over the predecessor's keep the predecessor's bytes past the new content. All of these look like structured, real data, because they are real data from somewhere else.

**Check / fix:**
- Search the slack verbatim (using a 64-256-byte window) in:
  1. the same resource's compressed input, at any offset (in-place residue);
  2. every other file on the disk or image, comparing `slack[k]` with `other[k]` at the same relative offset (buffer reuse in the disk build);
  3. the predecessor or sibling game's same-named file.
- An exact run (e.g. 256/256 bytes, or 4,945/4,946 at a constant delta) closes the question. Name the source and the mechanism in the doc, and size the real content from where the match starts.
- Use the real content size elsewhere: a map that is really 160×100, not 160×101 with a "trailer", removes `usableHeight − 1` workarounds downstream.
- Dedupe "found" records against the main region before counting them. Residue copies of real objects inflate object counts.

**Canonical example:** Hunter (Amiga). Tracks 50-51 held a 17-object chain documented as unprovable "without a second disk revision". From `0x3FB60` the disk bytes equal `objfile` at the same relative offset (`disk[0x35C00+k] == objfile[k]` for k in `[0x9F60, 0xB3F2)`, no exceptions), so the chain is a copy of objects already counted. That brought the object count to 197 unique objects. The `musfile` tail matched `soundfile` SFX sample 7 on 4,945/4,946 bytes at a constant delta, so it was not an 8th instrument. `jfile`'s slack equalled `epic` at the same relative offset.

**Variants:**
- War in Middle Earth `MMAP`: the "96-byte trailer / row 100" was a 256/256 byte-exact copy of the resource's own compressed stream at offset 7,487. The real grid is 160×100 = 16,000 cells, exactly the DOS `PAMM` size.
- Phantasie II: dungeon and message files were authored over Phantasie I's. P2 `DNG1` carries P1 `dng1`'s "A STRANGE PURPLE GAS F" string, so bytes past the last referenced line or slot are residue.

Related: `proven-residue-does-not-bound-region-start.md`, `bytecode-residue-recurring-groups.md`, `file-named-dummy-may-hold-real-leftover-content.md` (the opposite risk), `whole-corpus-count-is-scoped-to-reader-coverage.md`.

**History:** 3 projects (Hunter, WIME, Phantasie), 2026-11 audit sweep.
