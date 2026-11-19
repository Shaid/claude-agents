# vista — corpus notes

Project: `~/Development/vista`. Not games: **Vista Pro 3.05** (Virtual Reality Laboratories) and **World Construction Set 2.04** (Questar), Amiga terrain-rendering software, reverse-engineered with the same seer layout and method. All format facts live in `docs/rendering-algorithms.md`; this file is a pointer and history summary.

## History

- **2026-11-19 — first curation**, from the 2026-11-18 codebreaker audit round (`docs/<title>/audit-2026-11-18{,-changes}.md`, commit 7c2b0a8).
- WCS `.elev` layout corrected: files are `f4+1` west→east lines of `f8` south→north **signed** int16 samples (14,955 negative samples in one file). Every earlier parser test was a synthetic round-trip of the code's own row-major unsigned assumption; `src/terrain/__tests__/wcs-retail.test.ts` now tests retail files.
- The audit cited a square-tile seam test as layout proof; at apply, a null control showed it cannot see transposition (20 + 20 shared edges either way). The non-square `Deformatio.elev` (300×151; 1.05 vs 1.57) and header origins settled it.
- Vista Pro generator/material passes are verified word-for-word against the native code under a Unicorn M68000 harness (`tools/vistapro/native_harness.py`).

## Lessons sourced from this corpus (full list)
`check-that-cannot-fail-is-not-evidence.md`, `test-fixture-encodes-same-wrong-model-as-implementation.md`, `file-offsets-vs-segment-relative.md`; method: `game-re-method/verification-techniques.md` § Seam continuity (square-tile transpose blindness)
