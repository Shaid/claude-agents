# A "whole-corpus" count covers only what the reader parses; measure what it leaves

**When it bites:** you quote "1,046 directories, 24,472 records, whole disc, no cap", "no reference to X anywhere in the program", or "the table ends at entry N". The number came from a shared reader that parses the first directory per entry, decrypts one ROM bank, or stops at the last slot it knows the name of.

A clean walk with zero offset failures says nothing about bytes the walk never reached. Containers concatenate further directories after the first one's payload. Program images span several banks or SIMMs. Headers grow a new section slot that older files leave zero. Tables continue past the last named entry. Every downstream census and negative inherits the reader's blind spot, and nothing errors.

**Check / fix:**
- **Slack census:** for every container, compute `containerEnd − end of the last parsed payload`. Anything bigger than alignment padding (for example ≥ one sector) is a lead. Check whether it starts sector-aligned with the same header shape as what you already parse, and walk it.
- **Tiling with the format's own accounting:** where the container declares lost or free space, check `uncovered bytes == lost_space`. A mismatch means unindexed, often superseded, data. Warn against raw byte scans of that container.
- **Program space:** compare what you decrypt or disassemble with the full address map the reference emulator builds. Scope any static negative ("no reference to …") to the part you actually covered.
- **Header slots:** for every header offset/count field, check whether it is non-zero in any file. A field that is non-zero in a subset and points exactly at "extra records" is a new section, not a miscount. When a table you know the game uses is missing from the labelled entries, resolve every header pointer slot in ascending target order before concluding it is built in code: the gap to the next slot's target is the table's exact size, which checks the record layout for free.
- **Tables past the last named entry:** read on until the records stop satisfying the record invariant, then check for size-0 slots.
- In docs, label counts as "first-directory only" (or similar) until the reader is fixed.

**Canonical example:** Valkyrie Profile 2 (PS2). 89 TOC entries had 2,048 B to 41.5 MB of slack after the first directory's last payload. The slack was not padding: 883 more ordinary directories, all sector-aligned (883/883), 747,634,844 B (about 16% of the disc), 0 cumulative-offset failures. They held 5,490 MINA, 5,119 GIS, 442 ECAF (against 85 known) and an unseen `ESP\0` tag. Every "whole-disc" MINA/ECAF/GIS count was first-directory-only.

**Variants:**
- SFIII3 (CPS3): only SIMM1 was decrypted. SIMM2 decrypted to 1.6 M non-blank dwords of structured data, so every "no reference to `0x040c0094`" negative covered half the program space.
- 13 Sentinels / Unicorn Overlord `.mbs`: "extra drawGroup records past the declared count" were a 12th section with its own u64 offset at header `0x108`. It is non-zero in exactly 169 of 1,162 files and starts exactly at the drawGroup end (169/169).
- FF8 `battle.bin`: the table ran 7 LZSS overlays past the documented last entry `MAG337` (`hdr == size−4`, 7/7), then 5 size-0 slots.
- AESOP `EYE.RES` (Dungeon Hack): 2,399,876 B (35%) sat outside every directory while the header said `lost_space=0`. Each gap walked as a chain of 12-byte entry headers holding older versions of indexed slots. `HACK.RES`/`OPEN.RES` uncovered bytes equal `lost_space` exactly.
- Fire Emblem Fates `GameData.bin`: move-cost, weapon-type/kind and rank tables had no labels and a `code.bin` scan found nothing. They hung off unparsed data-header pointer slots; the move-cost matrix (count 16, then 16×16 B) ended exactly at the next slot's target and matched 169/170 cells of a published terrain table (shifted-row null 129/170, transposed 48/170).

Related: `no-traced-reader-region-is-not-proof-of-filler.md`, `shallow-magic-scan-undercounts-sibling-magic-corpus.md`, `content-type-absence-needs-multiple-independent-angles.md`, `slack-matching-another-buffer-is-build-residue.md` (when the slack turns out to be leftovers).

**History:** 6 projects (VP2, SFIII3, 13S/UO, FF8, Dungeon Hack, FE Fates), 2026-11.
