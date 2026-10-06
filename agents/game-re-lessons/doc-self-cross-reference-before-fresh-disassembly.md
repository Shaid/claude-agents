# A doc's own already-solved section can silently answer a different section's "still open" row

**When it bites:** about to start fresh disassembly, a census, an escalation, or a "needs live capture" verdict on an item the project's docs call open. Also: writing or auditing a `> Correction` that supersedes an earlier claim (stale copies survive elsewhere). Also: a mature campaign's open rows have run dry and you need a cheap proactive staleness sweep.

Docs built over many sessions solve the same fact twice under two names, or solve it once in section A while section B (or a source comment, a summary string, a verify script) still calls it open or asserts the refuted version. Nobody grepped before writing B, and nobody swept for copies after correcting A. The newest or most confident-sounding text is not automatically right, and neither are same-day date stamps (physical position in the file is the better write-order signal).

**Check / fix — before any new work on an "open" item (first move, not a fallback):**
- Grep the whole doc tree, `TODO.md`, and shared decode-library source comments (`tools/shared/*.ts` module JSDoc) for every key the item names: exact address, field offset, type/tag/region number, the mask constant and its complement halves (`0x20000`, `0xfffd`), the `TODO.md` id string, the asset/file name, struct name and stride constants. Doing this "earlier in the session" doesn't count; repeat it before writing up or escalating. "Grepped docs for X: no hits" is a required row in the paths-tried table.
- If an address grep is empty but the code's fingerprints (offsets, callees, constants) look familiar, disassemble back to the real prologue and grep that address, plus the callees and constants. Docs often cite an interior landmark, not the function's entry point.
- Check any fully-enumerated id/opcode→field table (SETPROP/GETPROP, event codes) for the field. Script-set property operands are static bytecode, so a corpus census answers "does it ever leave the default" without emulation.
- A narrow finding ("found for slot X, not checked elsewhere") may already be the general answer. Apply it corpus-wide.
- Run the project's full test suite before calling a finding new. A passing describe-block that names the mechanism means prior work already covered it.
- A grep hit on an "open" marker is not proof the item is open. Grep forward for a later, higher-numbered section; check whether a `tools/**/verify-*<topic>*.ts` exists and `git log --oneline -- <path>` it; grep `TODO.md` for the literal id (`resolved` there is decisive).
- A claim citing "see § N" earns nothing until you open § N and confirm it states *that* fact, not an adjacent one.
- A published negative census ("these N opcodes never occur") falsifies every positive claim elsewhere about its members. Join on the census key (opcode number, enum value), not wording. A running tally ("N writers as of round M") must be re-checked against every sibling doc covering the same function or overlay.
- If the doc's prose count disagrees with its own list, re-verify every list entry; one doesn't belong.

**Check / fix — when writing or auditing a `> Correction`:**
- Grep the refuted phrase in both directions of file order across all docs, source doc comments, source data-array `summary`/`description` strings, and `confidence`/`status` enums (grep for `'hypothesis'`/`'unknown'`). Don't trust a prior round's "N further stale copies fixed" tally. Under budget, fix cross-file copies before same-file next-section ones.
- Read the paragraph directly after every Correction block, where the unstruck old conclusion usually sits. Grep each offset cited inside Correction blocks against sibling docs' per-field tables.
- If a Correction says another section "was never updated in place", read that section and `git log -S '<phrase>'`. The fix may have landed in the same commit.
- If a Correction lumps several addresses under one struct-identity verdict, re-disassemble each one's base-register provenance, since one offset can belong to two structs. Recompute any `lui/addu/lw` table base from its operands instead of trusting the cited hex.
- If the superseded claim was "every"/"all N"/"exhaustive" and a committed `verify-*.ts` produced it, re-run the script in the same commit. Rewrite any failing assertion to the exact corrected invariant ("5 of 6, one exception at X"), never a tautology.
- "What's implemented" tables, `plan.md` "next steps" checklists, and source structs that carry fewer fields than the doc table go stale too. In that last case the doc is usually right and the shipped data is behind.
- Fix each stale copy with its own `> Correction` block, never a silent edit. A wholly stale `plan.md` section gets replaced by a pointer to `TODO.md`, not patched line by line. Cross-check a low-confidence enum hit against every later doc section touching the same address, not only its own table row. When auditing field doc comments, read the *sibling* fields' comments in the same block. A doc's earlier, more cautious wording is often the tell that a later, more confident correction overreached.

**Check / fix — proactive sweeps (no specific item in hand):**
- Cross-doc token sweep: regex out `ident+0xHEX`/`ident[0xHEX]` tokens from two docs that cover the same struct, intersect them, and read the shared ones side by side. Before "fixing" a hit, read a paragraph-wide window, because a nearby disclaimer may already explain it. Also skip hits inside a section already under dense same-day "Round N" audit.
- Id-diff sweep: extract every `<project>-<slug>` id from `docs/**/*.md` and `plan.md` and diff against the current `TODO.md` rows. For each mentioned-but-gone id, look forward for a closure and add the missing pointer. Strip `^\s*(>\s*)*\s*` and join lines with an *empty* separator before matching, or ids wrapped at a hyphen get truncated. Hand-check survivors that end in `-` (wildcards like `vp1psx-battle-*` aren't ids).
- Marker sweep: `grep -n "unnamed\|not yet named\|role open\|not proven\|still unnamed"` over the doc tree finds untracked residuals that are often answerable by cross-reference.

**Canonical example:** Valkyrie Profile (PSX, `valkyrie`). A 6-angle static census across every overlay and 650+ behaviour modules for the writer of `word[actor+0x570]` was written up as a hardened negative and escalated to `re-codebreaker`. The escalation's first move, `grep '0x570' docs/`, found the answer verbatim in `battle-logic.md`, committed four hours earlier by a sibling session. Every census angle had searched code, and none had searched the docs.

**Variants:**
- Black Crypt (Amiga, `crawl`): a "still open" `$51A(A5)` row was answered by a 13-entry per-level table that was already **SOLVED** in another section, which even listed `$51A(A5)` as a reader.
- FE: Three Houses (Switch, `chimera`): a "roster array NOT found" section sat ~13,000 lines after a section that had solved it (stride `0x24C`) and shipped a patch. An escalation brief saying "only found on the old format" should itself trigger the grep (see `reference-tool-data-revision-mismatch.md`).
- `valkyrie` r212: "runtime-only, needs live capture" for `actor+0xee`/`+0xb8`. §12.2's SETPROP table already listed both, and a static census found 39/43 and 55/60 operands away from the default.
- `valkyrie` VP2: the "mystery" `onoda` tag at FIS+20 was already characterized as an exporter tag at `0x14` in `ps2-fis-image.ts`'s own header comment.
- Phantasie III (Amiga, `nicodemus`): a newer "done" block called `Dng.csh` a flat backdrop, but an older section had correctly found an icon bank.

Related: `working-tree-may-already-solve-a-docs-open-item.md` (code ahead of docs), `field-centric-bit-census-blind-to-sibling-reuse-and-split-mask.md`.

**History:** ~31 recorded instances (`crawl`, `nicodemus`, `chimera`, and ~28 on `valkyrie`). Full log in `_archive/doc-self-cross-reference-before-fresh-disassembly.md`.
