# Before counting a check as evidence, ask what wrong model would fail it

**When it bites:** you're about to cite a check as confirmation, or trust a test that has always passed. Many checks in RE pass by construction. They test the code against itself, against a quantity the code fixes, or against bytes identical to the input.

Before citing a check, name one plausible **wrong** model (wrong field, wrong stride, shifted offset, wrong codec) and run the check on it. If that wrong model passes too, the check is not evidence. Recurring shapes:

| Shape | Why it can't fail | Discriminating replacement |
|---|---|---|
| "0 out-of-range indices" when the index type can't exceed the table (u8 cells vs a 260-tile bank; depth-5 pixels ≤ 31; any index into a 700-tile flat bank) | the range is guaranteed | `max(index) == count−1` per field, with a wrong-count/shuffled-pairing control (true: 62/62 maps; shuffled ≈0.8%) |
| "index in range" when the field is constantly 0 | 0 is always in range | the same `max == count−1` test on every candidate field (Muramasa: u16 @+4 642/642, @+6 37/642) |
| "renders non-blank", "distinct values > 1" | random bytes pass | a cross-game/cross-port pixel equality, or a seam/edge oracle with a shuffled null |
| "0 deviations" on records the parser only accepts when the invariant holds | survivor bias | report "accepted M of N candidates"; cite only checks the parser does not enforce |
| Expected value hand-computed under the same assumption as the code (pixel rect vs ×8 columns) | both share the bug | an independent source: the reference engine's code, a sheet-coverage census |
| Cross-port/cross-disc "byte-exact" on inputs that are byte-identical | same bytes in, same bytes out | hash-join the inputs first; aim the test at the entries that differ |
| Two implementations (Python vs TS) or a round-trip through an encoder written from the same spec | one hypothesis twice | an independent oracle: live RAM, a third-party decoder, a second port |
| Comparing the new renderer with the project's own earlier renderer or formula | self-referential | a real game frame, or the game's own routine |
| Seed/whitelist heuristics that contain the answer | circular | a seed-agnostic scan (exact tiling + checksum) giving a unique hit |
| The last record of a greedy walk "ends exactly at EOF" | the walk ends where the data ends | check the interior records |
| "Lengths sum exactly to a suffix ending at EOF" when the code sets `bodyStart = EOF − Σlen` | the suffix is defined by the sum | compute the start **forward** from the header and require Σlen to land on EOF; the wrong unit is the null (SotB2 tracker samples: words → residual 0 on 3/3 modules, bytes → 43,996 / 34,440) |
| "N/N" measured on the sub-population the sampler reached (only nested containers, only small roots) | the excluded class is never tested | census each structural class separately (disc-level vs nested, first vs later record); Drakengard fpk `data_start == 0x80+[0x18]` was 467/467 nested and failed all 7 disc-level archives |
| "Decodes with exact input consumption" cited as proof the source bytes are intact | decrunchers without an integrity check still consume exactly on corrupted input | bit-flip null (SotB3: 27/40 flipped inputs still decoded exactly); authenticate the source against an external CRC/hash set (WHDLoad CRC tables, redump); say "faithful to the routine", not "verified bytes" |
| An aggregate % over a population ("82.4% agreement") | hides whole failing units | score per unit (per level, per file) and list the failures |
| A test that pins the observed exception count | passes only while the bug exists | assert the invariant, not the current count |
| A footer/checksum from a **self-resynchronising** cipher's final state | ignores the initial key and most of the payload | flip random bits and vary the initial key; count detections |

**Check / fix:** for each cited check, write the one-line "this would fail if …". If you can't, downgrade it to "consistency check" in the doc and find a discriminating one. Keep the null-control numbers next to the claim.

**Canonical example:** Eye of the Beholder (Amiga/DOS) wall-decoration rects, "pixel-exact: 193 px, bbox (65,32)-(73,56), 9×25 px". The expected placement was computed with the same "rects are pixels" assumption as the renderer. ScummVM's `encodeShape` uses `x<<3` and `w<<=3`, and the max `x+w` is exactly 40 (= 320/8) in 10 of 11 files. The ×8 reading covers 0.90–1.00 of each sheet's opaque pixels; the shipped pixel reading covers 0.12–0.23. Every decoration in three walkers was drawn at 1/8 width.

**Variants:**
- Frontier: Elite II save footer matched 5/5 saves, but the cipher resynchronises. Any initial key reached the same footer, and 0/200 random bit flips were detected.
- VP1 PSP "strongest confirmation, 0 differing bytes": 1,123/1,123 room entries were byte-identical to PSX Disc 1 input.
- Dungeon Master CSB `MINI.DAT` location: the seed whitelist contained the answer's own seed. A seed-agnostic exact-tiling + byte-sum scan found the same unique hit.
- Gold Box Dark Queen GEO "82.4% average agreement": 8 of 20 levels were transposed (per level 0.09 → 1.0 after swapping width/height).
- World Construction Set `.elev`: every parser test was a synthetic round-trip of the code's own row-major unsigned model; real files are transposed and signed. Only retail-file tests caught it.
- Shadow of the Beast 1–3 screens "confirmed" by sitting on a hard-coded verified-screen list: relabel list membership as such, not verification.

Related: `decoder-output-length-check-is-tautological-assert-input-consumption.md` (the codec case), `rle-decode-succeeds-on-garbage.md`, `test-fixture-encodes-same-wrong-model-as-implementation.md`, `one-based-first-index-sum-is-total-minus-one.md`, `tracker-prose-is-not-evidence.md`; oracles that can fail: `game-re-method/verification-techniques.md` § Seam continuity, § Shared-wall reciprocity, § Field identity by `max(field) == count − 1`.

**History:** ~45 instances across ~18 projects in the 2026-11 audit sweeps (crawl EOB/Wiz6/Gold Box/DM, nicodemus Phantasie, vanille, strike, valkyrie, middilgard, wyrm, hunter, siren, methanoid, facepunch; 2026-11-18 round: moonstone SotB2/SotB3, flower Drakengard, vista WCS).
