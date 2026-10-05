# A 100% "uniquely best" offset fit is still noise when the validity oracle is "target slot non-empty" in a dense range — confirmation needs an identity-grade oracle

**When it bites:** a small numeric id field is resolved to an archive/table
index by brute-force additive-offset sweep, the winning offset hits
**100%** (or near it) of the field's values, the sweep even reports it as
"uniquely best" — and the acceptance test for each hit was merely that the
resolved target slot *exists / is non-empty / parses*, in a target range
that is mostly populated.

In a dense range, "slot non-empty" has a base rate near 1, so a contiguous
block of field values (sequentially-allocated ids are almost always
contiguous) will fit *perfectly* at many offsets; "uniquely best" then just
means every competing offset happened to graze one of the range's few
holes. The hit rate cannot distinguish the true offset from a wrong one —
only an **identity** check can: does the content at the resolved index
actually belong to the row that referenced it?

Confirmed on Fire Emblem: Three Houses (`chimera`, Switch): the AssetID
table's `sothisFusedID` field (values 71–97, one per timeskip-aging
character) was "confirmed" in project docs at `+3049` on a 31/31 (100%),
uniquely-best offset sweep against non-empty DATA0 pack slots — and shipped
into `asset-id-table.ts` as `SOTHIS_BASE`. A later pass refuted it in
minutes with an identity check: under that base, MByleth's value resolves
to his own *regular* body, Dimitri's to **Edelgard's** academy body, and
values 71–82 land on the regular bodies of Randolph/Anna/Jeritza/Rhea —
unrelated NPCs. The field turned out not to be a body-pack id at all (it is
a per-character hair-variant id in a different id space). Meanwhile the
*same* sweep technique's `+3120`/`+3620` body/head fits from the same pass
were genuinely correct — the difference is they had independent identity
anchors (Byleth's known `pack_3120`, visual renders of resolved models),
which the `+3049` fit never got.

**Fix:** an offset sweep's hit rate is only evidence when the per-hit
acceptance test has a low base rate. In a dense target range, always follow
the sweep with at least one identity-grade check per distinct referencing
context: resolve 2–3 values whose owners you know and verify the target's
*content* matches that owner (render it, compare its skeleton/texture to
the owner's other assets, cross-check a name list). A fit that maps row X's
value onto row Y's known asset is refuted no matter how clean its
percentage. Sibling files: `weak-single-offset-fit-signals-missing-
indirection.md` (an 80-95% fit = look for an indirection layer);
`partial-resolution-rate-is-noise.md` (40-70% = the field reading itself is
wrong). This file is the third regime: ~100% but meaningless, because the
oracle couldn't fail.

**Second confirmed instance — a subset-true fit can be one BRANCH of a
windowed resolver (same game, the DLC-outfit `modelId` field).**
`3120 + modelId` fit all 21 outfit-table values against non-empty slots
and even had real code behind it (`FUN_3CD70`'s `id < 900` branch — the
genuine, disassembly-confirmed BODY_BASE site) — yet it was only *true*
for the two sub-500 ids. Ids in [500,570] first receive a `+400`
displacement into a [900,1067] window resolved against a different base
(`34810 + id`, the AOC/DLC merge window; net `dlcLocal = modelId − 13`).
The tell: exactly the low ids decoded to correct content while the 5xx
ids decoded to *well-formed but wrong-kind* content (numeric collision
onto the head window — `HEAD_BASE = 3120 + 500`). When an additive fit
verifies for one value subset and produces plausible-but-wrong content
for the rest, don't hunt a better single constant and don't average the
evidence into "70% confirmed" — hunt the **window-boundary comparison
constants** (`cmp #500`/`#570`/`#900`/`#1067`-shaped guards) around the
confirmed base site: the fit you have is likely one branch of a range-
gated resolver whose other branch nobody has found yet.
