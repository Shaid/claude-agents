# A specialist escalation's — or any prior session's own — returned claim can be stale or false even when it sounds specific and confident

**When it bites:** promoting a `re-codebreaker`/`re-oracle`/subagent result (a "solved" verdict, a probe script, cited addresses, a coverage number) into a committed extractor or doc. Also: building on a prior round's or your own past session's "visual check confirms X" / "needs deeper tracing" claim. Also: a specialist flags an already-shipped asset as wrong.

A convincing final render or a precise-sounding number does not make every artifact or detail handed back with it true. Scripts drift after the renders were made; byte citations are transcribed by hand; aggregate percentages sit next to false per-item details; a "visual check" sentence may describe a check nobody actually looked at. Treat the **prose claims** (struct layout, formula, disassembly citations) as what to re-verify, with fresh code — never copy the returned script, and never recite a report's check as if it were evidence. This is a fixed, small cost of every promotion (typically minutes), not a step reserved for suspicious results; most passes find nothing, and that earned confidence is the point.

**Check / fix:**
1. **Re-implement from prose, not code.** Write a fresh decoder from the claimed layout/formula and run it against real bytes; cross-check its output against the specialist's own rendered evidence pixel-wise (sample a known background colour).
2. **Byte-compare every cited offset** against the real file (`file[off:off+n] == claimed hex`) before writing addresses into docs — then **re-derive the interpretation** too (JAL target `(w & 0x3ffffff) << 2`, `lui`+`lw` effective address with sign-extended low half, decoded immediates). A correct transcription can still carry a wrong computed address.
3. **Diff any disassembly excerpt** the specialist worked from against the project's canonical disassembly for the same range.
4. **Re-run verification yourself**, with your own driver and inputs, instead of reading its "0 mismatches" summary. Use *generic* code over every value actually present in the corpus — a verifier built from hand-written `if/elif` branches per observed kind reports a precise N/M that silently excludes kinds it never branched on.
5. **Check each specific claim, not the headline.** A correct aggregate can sit beside a false per-item detail.
6. **Demand a denominator.** "X is essentially a function of Y" backed by a list of confirming examples is hiding its failures — re-run it as a census over the whole population and record the percentage (a ~60–70% match is a hypothesis, not a decode).
7. **Re-derive keys of keyed mappings** (jump table case→handler, opcode→handler, id→resource) from raw bytes even when every entry's content verifies; a transposed pair survives content checks.
8. **Before acting on "shipped asset X is wrong,"** read the code path that actually produces X — watch for same-basename siblings differing only in extension/case.
9. **Before spending a round on a previously flagged structural anomaly,** re-read the bytes skeptically; the anomaly may be a misread.
10. **Reproduce "I checked, it's fine" with an independent oracle** (a real browser screenshot, not a re-run of the same code path that would confirm its own bug).

**Canonical example:** Wizardry 6 Amiga `.PIC`: the escalation was genuinely right (cel-drawer disassembly, length formula byte-exact over 731 cels, legible renders), but its saved probe script held the standard EGA palette order, not the permuted order its doc and disassembly claimed. Sampling background pixels in the escalation's *own* PNGs matched the documented table, not the script's array literal — the script on disk was not the one that made the renders. Re-deriving from prose avoided committing the stale array.

**Variants:**
- *Coverage gap behind a clean percentage* — VP2 PS2 mesh escalation's "99.97% unit normals" only branched on 2 of 4 normal encodings, skipping `V3-16` (~84% of batches) and a 1-component `V1-8` that yields `NaN` as 3D; a generic port caught it (`valkyrie`).
- *Per-item detail false beside a true aggregate* — Wizardry 6 SNES maze escalation: ~99% agreement held, but only 1 of the 3 "768/768 exact" levels was exact, and an unflagged level was the worst.
- *No denominator* — Phantasie III (`nicodemus`): a "function of neighbour mask" claim evidenced by ~20 examples was 195/311 (62.7%) as a census; the sibling claim stated "58 of 58" re-ran exactly and was kept.
- *Transposed keyed mapping* — Spirit of Excalibur: a fork's 9-case jump-table map had cases 6 and 8 swapped; caught by decoding the raw `DC.W` displacements.
- *Misattributed shipped asset / false self-report* — Champions of Krynn (`crawl`): `walldef-1001-*.png` came from `8X8D1.DAX`, not `.DAA`; Parasite Eve (`parasite`): a prior session's "Playwright check confirms plausibility" was false — every model rendered collapsed (`length-invariant-blind-to-track-index-misalignment.md`).

Related: `hand-computed-test-fixture-vs-real-run.md` (the reviewer's own hand-derived fixtures need running too).

**History:** 13 recorded instances (Wizardry 6 Amiga/SNES, Black Crypt, WIME, valkyrie VP1/VP2, nicodemus, Spirit of Excalibur, crawl, parasite) — full log in `_archive/verify-escalation-artifacts-not-just-claims.md`.
