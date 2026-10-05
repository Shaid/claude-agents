# A TODO.md/plan.md status claim — or a confident corpus-count number in the spec doc itself — survives unverified across session boundaries unless you re-derive it

**When it bites:** you're about to build on a TODO.md/plan.md row, a spec-doc count/label/"byte-identical" claim, or a code comment ("convention established in X") without opening its evidence. Also: a cited reproduce-script is missing, or its prose under-states its scope. Also: you're continuing a multi-round compliance sweep, or trusting a stored snapshot of an external project's progress.

Tracker files point at evidence; they don't contain it. A well-written status row ("independently re-verified, e.g. record 5 decodes to a legible 7-species group") reads exactly like a verified one, and it gets copied forward by later summaries that never re-checked it. Repetition across sessions is not corroboration. The same holds for spec-doc tables, code comments that cite other code, and stored notes about third-party projects. Distrust is not disproof, though: it means re-running the derivation, and an old claim that survives that re-run is a real result.

**Check / fix:**
- Before building on a row, open the doc section its Evidence column names. If the *specific* claim isn't there (not just related material), re-derive or refute it from scratch. It costs one `grep`/`Read`, so do it for every row you build on.
- **Corpus counts:** re-derive with a walker that mirrors the production code path (e.g. a container-name histogram, not a leaf-only scan) before you plan around explaining a "gap" against the number.
- **Dead reproduce-pointer** (`git log --all --follow <path>` finds nothing): re-derive anyway. **Prose under-states scope:** open and re-run the cited script before writing new code. The code, not the paragraph, defines what was checked.
- **"Registered/wired in consumer X"** claims: `grep` the identifier in the consumer file (viewer table, manifest, pipeline).
- **Spec-table labels:** a bit/field name is verified only if its row cites a SET (producer) site. A row that cites only the TEST site it was read at is a guess, however its formatting looks. Compare its evidence density with its neighbours.
- **Citation attached to the wrong sibling:** when one pass covered several similar items (adjacent ids, banks), check which item the cited slot actually belongs to, not just that it resolves to something real.
- **"Byte-identical across N copies"** + a helper that reads only copy A "because § N says identical": the executable proof covers a subset of the claim. Run the check on the other copies through the low-level primitives.
- **Code-comment citation chains** (script X: "convention from Y"; Y: "re-confirmed below"): read Y's code. Comments can cite each other with no live check at either end.
- **Compliance sweeps** (e.g. `grep -l 'build/cache' verify-*.ts | xargs grep -L 'vp-corpus'`): a hit count is a snapshot, not a ceiling. Re-run every *prior* round's query, diff against what was fixed, and don't remember "N found" as "N handled". Queries aren't supersets of one another. "Imports the live helper and mentions both discs" can pass a file whose *primary* claims read a module-level cached `readFileSync`. Skim each file per claim. Watch for `existsSync(cache) ? check : SKIP` (silently zero assertions) and "cross-disc" checks that compare two differently-dated cache files to each other.
- **External prior art:** "upstream solved N of M" is a dated snapshot. Re-clone/re-fetch before re-deriving or escalating.

**Canonical example:** Wizardry 6 (Amiga). The TODO.md row read "Section 6 is now confirmed (400×32B monster encounter/spawn groups, independently re-verified against the monster catalog)" and was carried across a session boundary. Nothing about it was in `data-structure.md` or any investigations file. A tree-wide `grep` for its own details found nothing. A fresh verification refuted it in under an hour: section 6 is a scripted event/opcode table (message triggers, probability-gated recursion, dice rolls), confirmed by disassembly and 174/174 and 46/46 field matches against the correct interpretation.

**Variants:**
- Drakengard (PS2, `flower`): the doc said "297 instances of `mmodel.bin` counted recursively" with no surviving probe. A walker mirroring `walkCaviaContainer` found **12**, which divides every shipped LOD/animation total evenly. There was no bug to explain.
- Millennium 2.2 (`methanoid`): two sessions said three tables were "registered in the viewer's Data tab". `DATA_SOURCES_BY_GAME` listed none of them.
- Parasite Eve II (`parasite`): a stored note said "community decomp solved 2 of 23 TMD families". A fresh clone had all 23 plus a working LZSS decoder.
- Valkyrie Profile (PSX, `valkyrie`): bit 13 labelled "ledge-grab" from a TEST site only (it is a lift-and-throw override). Bank 3606's "Dipan-past" citation actually belonged to bank 3607. `collectItemTable()` read Disc 1 only and cited § 5. `build/vm/verify.ts` was never committed (re-derivation reproduced every number; see `fresh-census-skips-projects-own-false-positive-filter.md`). An SLZ correction omitted subtype 0, but the script already checked it. A sweep query reported 11 hits, a re-run found 13 more, and 5 of 5 random spot-checks showed the mixed live/cache shape.

Related: `verify-escalation-artifacts-not-just-claims.md`, `local-decode-cache-may-be-stale-reverify-fresh.md`.

**History:** 13 recorded instances (Wizardry 6, flower, methanoid, parasite, valkyrie): full log in `_archive/tracker-prose-is-not-evidence.md`.
