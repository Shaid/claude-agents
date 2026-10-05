# A multi-instruction dataflow-chain census's total is an artifact of its lookahead window, not a property of the code, unless the window is liveness-based

**When it bites:** you're building, or trusting a doc's total from, a census of a multi-instruction register-chain idiom (`sll ; addu base ; load`, "reload pointer then access +X") that was matched by "look ahead K instructions". Also: a rescan reproduces the doc's exact count, which is not corroboration. Also: a windowed census script still passes while its label or header claims "the complete set".

A fixed lookahead window K is usually picked by feel, so the total measures K, not the binary. A window that is too wide lets an unrelated instruction re-clobber the register and matches a different idiom with a similar prefix. A window that is too narrow misses real chains at long distances. The resulting "N sites, 0 deviations" framing looks clean, so nobody re-checks it.

**Check / fix:**
- Assume any doc-cited multi-hop census total used a fixed window unless its method is stated (especially an uncommitted one-off probe or escalation result).
- Sweep several window sizes. If the total moves at all, it isn't a fact. Rebuild the scan as a liveness walk: follow the tracked register with no length bound, and abandon it as soon as another instruction writes it or at `jr $ra` (see `dataflow-chase-must-track-destination-not-mere-reference.md`).
- Diff the matched-address **set** against the doc's cited addresses, not just the count. A false inclusion and a false exclusion can cancel out.
- Tag every hit as load or store before you aggregate. A figure like "N register uses" can silently mix reads and writes.
- When the "other/unrelated" bucket shrinks, disassemble whatever is left in it. A loose census can file a real, new hit under the wrong field family.
- When auditing a committed census script, read its check labels and header comment separately from what the checks actually assert. If the labels claim completeness ("complete set", "not a sample") but the assertions only test the in-window result, relabel them to the true, narrower scope rather than changing the assertions. Such a script never fails, so use `git log -S '<phrase>'` or a liveness rescan to find a superseding finding, possibly in a sibling doc.

**Canonical example:** Valkyrie Profile (PSX, `valkyrie`), round 214. An escalation's doc claim said the `(sll ×32 ; addu base ; load)` idiom occurs at "11 sites: 8 on `s3`, 3 unrelated `+0xc84`". Fixed-window rescans gave 8/9/10/19/20/20 hits for K=1..6, and none gave 11. A liveness scan found 9: the same 8 `s3` hits (byte-exact on both discs) plus one non-`s3` hit. That hit read a previously undocumented byte that fed a previously unknown second writer of a shared field. The "3 at `+0xc84`" were an unrelated 4-instruction `sll+addu+addu+load` 2D idiom that the wide window had admitted.

**Variants:**
- Round 216, `battle-logic.md` §83.2: "all six reads of `instance+0x6/+0x8` inside one function". A liveness rescan also found 6, but one cited site (`0x8009d76c`) was a store, and a sixth real read lay outside the function. The "16 register uses" figure mixed reads and writes.
- Round 218, §94.4: a 15-instruction window reported a "COMPLETE set" of 3 sites. Liveness found 5, with 2 more at distances 30 and 63 testing a second mask. The script's `hits.length === 3` was still literally true, while a sibling doc's superseding fix never propagated back.

**History:** 3 recorded instances (`valkyrie` rounds 214, 216, 218). Full log in `_archive/fixed-lookahead-window-census-count-is-a-window-size-artifact.md`.
