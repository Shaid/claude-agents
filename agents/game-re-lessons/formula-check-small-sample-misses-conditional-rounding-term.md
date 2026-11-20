# An exact formula, "0 exceptions" invariant, fixed length or field role can pass 100% on a small sample while a conditional term hides in the rest

**When it bites:** a doc claims an exact relationship between decoded fields (`fieldB == f(fieldA)`), an "N/N, 0 exceptions" invariant ("always unscaled", "never has flag X"), a **constant header length**, or a **field role** ("u16@X is the format selector"), backed by a small or hand-picked sample that all passed. You are about to trust it at full-corpus scale, or re-auditing one that fails on a small, noisy-looking fraction. To find candidates systematically, grep the doc tree for "checked on N", "N samples", "verified (on|against) N", "across N slots": any small N attached to a confirmed claim is a candidate.

A conditional term (alignment padding, a flag-gated header block, a second sheet) only shows on records that need it. A small sample can easily draw no such record: at a 24/76 split, 10 straight passes is about 1 in 1,400, rare but not impossible. Nothing in the sample looks wrong, which is what makes it distinct from a prevalence undercount (`small-sample-probe-undercounts-dominant-subformat.md`).

**Check / fix:**
- Re-run the claim over the **whole population** the production parser/scanner enumerates, not a hand-picked run.
- When it fails on a nonzero-but-not-all fraction, don't file it as noise: **histogram the per-record delta** between prediction and reality. A tight small-integer histogram (`{0,1,2,3}`) means alignment; two values (`{0, 12}`) means an optional block. Find the bit or field that predicts the delta.
- **Before naming a field a selector, or a constant a fixed length:** find files where the field (or the suspected gating flag) takes a different value. Show that changing it changes the decode, and that the alternative reading (a count, a flag) fails on those files.
- Keep a null control: the old rule should fit ~0 of the records the new rule says differ.
- Keep the original claim in the doc as a `> Correction` block, since it records how the earlier pass verified.

**Canonical example:** Valkyrie Profile (PSX, `valkyrie`) SLZ container. `chainStride == 16 + compressedSize` was "exact for 10 samples". Over all 2,649 chained blocks it held for 24%; the others were 1–3 bytes larger. Real rule (0 exceptions over 26,911 headers): `chainStride = align4(16 + compressedSize)`. The 10 samples just never needed padding.

**Variants:**
- *Boolean invariant, non-random sample* — VP1 field-sprite parts: "unscaled 3136/3136" over 4 dungeon slots; corpus-wide (113,908 parts) 3,224 real exceptions. The renderer's disassembly two paragraphs above already named the general path the sample never exercised (`valkyrie`).
- *Fixed header length that is flag-conditional* — Koei Tecmo G1T (FE Warriors 3DS, `lucina`): per-texture header "always 20 bytes" is 20 when byte+7 bit `0x10` is set, 8 when clear. Check (table delta − mip-chain size): rule fits 13,604/13,648 (misfits are one container's span artefacts); null control: constant 20 fits 0/526 testable 8-byte-header textures.
- *Count read as a selector* — FE Awakening `.bfnt` (`lucina`): u16@0x1a was read as pixel format; it is the sheet count, the format is u16@0x18. All four sampled fonts had one sheet and the same format; the two unsampled ones (System: 2 sheets A4, Debug: 1 sheet A8) decoded wrongly.

**History:** 4 recorded instances (`valkyrie` ×2, `lucina` ×2) — verbatim narrative in `_archive/formula-check-small-sample-misses-conditional-rounding-term.md`.
