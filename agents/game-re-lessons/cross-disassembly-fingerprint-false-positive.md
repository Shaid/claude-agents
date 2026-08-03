# Cross-disassembly instruction fingerprints need a divergence point, not just a match

**When it bites:** translating an address/label between two different
disassemblies of the *same* binary (e.g. an old capstone dump using real
addresses vs. an IRA dump using its own label scheme) by matching a short
run of instruction text between them.

Two distinct failure modes surfaced in the same session (WIME/middilgard),
both from trusting a match too early:

1. **Short, generic runs match the wrong place.** A 4-6-instruction
   fingerprint built from common boilerplate (`JSR (PC) / ADDQ.W #8,A7 /
   MOVEQ #0,D0 / BRA.W`) matched a *different*, unrelated call site at only
   6/8 lines scored — the correct answer was a different function entirely,
   caught only by independently re-deriving the target from a DATA-hunk
   offset the citing doc already documented (walking forward from a known
   global read through the expected loop structure) and finding it
   disagreed with the fingerprint match.
2. **Two thematically-paired functions can share a byte-identical prologue
   *and* call the same shared tail sub-function**, differing only in what
   happens *after* that shared middle section. Two "ending dispatch"
   routines (Barad-dûr path vs. Mt. Doom path) were ~20 instructions
   identical — same screen-mode setup, same game-mode check, even a call to
   the exact same absolute target computed independently at each call site
   via `call_addr + 2 + PC-relative-displacement` — before finally diverging
   in their tail (different scratch coordinates written, different final
   parameters pushed to a shared icon-draw call). A fingerprint taken from
   the start of either would match the other.

**Fix:** treat a fingerprint match as a hypothesis, not an answer, exactly
per the project's general verification bar. Before recording a match as
confirmed:
- Cross-check at least one DATA-hunk operand displacement or literal
  constant in the matched region against something already independently
  documented (a global variable's known offset, a location-table
  coordinate, a string) — this is usually cheap since `A4-N` converts to a
  real DATA offset via simple arithmetic, tool-independent of either
  disassembly's labeling.
- If two candidate functions are suspected of being parallel/twin routines
  (win vs. lose, two similar event handlers, two similar per-faction
  variants), read *past* the first several matching instructions to their
  actual divergence point before trusting either identification — the
  divergence is often where the real distinguishing behaviour (and the
  correct label) lives.
