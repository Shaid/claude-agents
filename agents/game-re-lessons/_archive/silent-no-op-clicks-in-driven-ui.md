# Archive — raw instances behind `silent-no-op-clicks-in-driven-ui.md`

## Instance 2 — 2026-11-04, `methanoid` (Deuteros, Amiga): press length vs main-loop poll phase

Verbatim from the harvest candidate
(`20261104-140205-methanoid-click-press-length-phase-artifact.md`), source
evidence `docs/deuteros/amiga/data-structure.md` § third-pass slot table
"Correction (fourth pass, 2026-11-04)" and
`tools/deuteros/emu/live_probe.c` (`click X Y [btn [press]]`):

> When an injected click is dispatched only at one coordinate (or
> intermittently), suspect the press length versus the game's polling
> cadence before inventing hover/state hypotheses. A press shorter than one
> main-loop iteration is missed depending on phase. Make press length a
> harness parameter (200 slices reliable vs 40), then re-run with the hit
> rectangle's exclusive edges (x2/y2) as null controls and the full y range.
> Deuteros slot 98: "only x=620,y=114" collapsed to 11/11 y values across
> x576..658, y107..120 once the press was lengthened.

Project-doc detail, kept here rather than in the lesson:

- Table `$2202A` (hdr 2): slot 97 = x 512..576, slot 98 = x 576..658,
  y 107..120. Half-pixel X, pixel Y, `x2`/`y2` exclusive.
- Repro from a fresh Self-Destruct page: `poke 1301E FFFF 2`,
  `poke 1A126 1 1`, click panel 60,128, settle 15000, then `click 600 112`
  as the first click after the page opens.
- 40-slice press: dispatch depends on absolute slice phase; a leading
  `run 200` flips 1 dispatch to 0; 5 clicks at settle 15000 gave 0/5.
- `PRESS=200`: 5/5 at settles 40000 and 100000, 4/5 at 15000. `PRESS=150`
  and `400` also dispatch the failing phase.
- Null controls: nothing dispatches at x = 658/660 or y = 106/120.
- Scripts: scratch `w4/sweep*.txt`.
- Also noted in the candidate, excluded from the lesson as per-game format
  detail: hit-record `id` fields are UI-string message indices, so ids were
  resolved against the shipped string table's name slots statically in bulk.
