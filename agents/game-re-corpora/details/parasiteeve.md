# parasiteeve — Parasite Eve (PSX)

**Project root:** `~/Development/parasite`
**Game/platform id:** `parasiteeve` / `psx` (SLUS-00662)

Squaresoft, 1998 — same era/team lineage as FF7/FF8/FF9 (pre-rendered 2D
backgrounds + 3D polygon character models, standard PSY-Q SDK toolchain,
confirmed via `$Id: bios.c,v...` debug strings in the exe). All data ships
inside one flat container, `PE.IMG`, addressed from a static table in the
main executable `SLUS_006.62`.

## Solved

- **562 standard PSX `TIM` bitmaps** — UI/HUD/font/logo graphics, found by a
  whole-file TIM magic+header scan. Shipped as
  `public/assets/parasiteeve/psx/textures/`+`palettes/`+`screens/`.
- **Actor/character resource package table** — a static 438-slot table at
  `SLUS_006.62+0x83b78` (413 populated, 8 bytes/entry: `u32 sectorOffset` +
  packed `u32` chunk1/chunk2/chunk3 sector-length triple), confirmed
  byte-exact by a zero-deviation self-consistent chain
  (`entry[i].sectorOffset + chunk1+chunk2+chunk3 === entry[i+1].sectorOffset`
  across all populated entries). Each entry is one character/enemy's 3-chunk
  resource bundle inside `PE.IMG`. See
  `tools/parasiteeve/actor-packages.ts`.
- **Actor-package chunk container** (shared shape across all 3 chunks): `u32
  endOffset; u32 sectionBOffset` header, then a "section B" directory at
  `sectionBOffset`: `u32 packageTag` + 12 packed slots
  (`count:10 bits | offset:22 bits`, chunk-relative). See
  `tools/shared/psx-actor-chunk.ts`.
- **Chunk1/chunk2 = VRAM texture pages.** Slot 9 (populated only in
  chunk1/chunk2) is a 20-byte VRAM-upload descriptor
  (`byteLength; srcOffset; RECT.h; RECT.w; packed(x,y)`); confirmed
  `byteLength == w*h*2` for 8,217/8,217 records. Chunk2's pages carry
  character body textures. Chunk1's pages (always VRAM x=768/832) are
  **the tile-scatter background system's own texture bank** — see
  "Prerendered backgrounds" below; `pe-actor-chunk1-consumer` is closed,
  resolved positively, after two earlier `ghidra-disasm` passes each
  wrongly reaffirmed it as dead data (see the pitfalls this surfaced,
  cited below). See `tools/shared/psx-actor-vram.ts` and
  `tools/shared/psx-tile-scene.ts`.
- **Chunk3 = 3D models + skeletal animation directory**, cracked whole-corpus
  by a `re-codebreaker` escalation (Python reference in
  `build/cache/parasiteeve/re-codebreaker/`) and ported to TypeScript
  (`tools/shared/psx-actor-model.ts`,
  `tools/shared/psx-actor-model-gltf.ts`). Model header (40 bytes, signature
  `h[12]==31 && h[15]==1 && h[17]==255`) gives bone/vertex/primitive counts;
  a 12-byte bone table (`firstVertex` 1-based, `vertexCount`, `parentIndex`,
  `boneLength`, `translationZ`) satisfies a zero-deviation invariant
  `translationZ == -parent.boneLength`; vertices are **bone-local**
  (confirmed via bbox/overlap testing, not global-space); a 12-byte
  primitive array (textured quads/tris carrying a `(0x80,0x80,0x80)`
  neutral-tint sentinel, then untextured quads/tris with real RGB and no
  sentinel — see
  `validation-sentinel-scoped-to-sub-region-not-whole-array.md`) plus a UV
  tail anchored to the *end* of the declared model size. **136/136 models**
  across the full 414-entry table decode and bake to textured glTF+PNG,
  validated pixel-exact against the escalation's reference renders and
  structurally with `@gltf-transform/cli` (0 errors). Texture baking uses
  the "UV-space unwrap" trick (draw each primitive at its own raw UV
  coordinates, sample the source VRAM texture at the same (x,y) — the
  canvas becomes a standalone atlas addressable by `(u/255,v/255)` with no
  packing math) — see `game-re-method/verification-techniques.md` § "UV-space
  unwrap texture baking". Porting the reference decoder surfaced two
  generalizable pitfalls (a UV/index winding mismatch, and a validation
  sentinel scoped to the wrong sub-region — see the pitfalls index).
  **Pose assembly: rotation confirmed genuinely absent from the model
  header/bone table — then found and SOLVED in the animation-clip
  resource.** A follow-up session first re-investigated bind-pose assembly
  (task scope: derive the REST pose from the bone table alone, not full
  animation) and confirmed by direct per-bone vertex-extent measurement
  that meshes are stored in a canonical local rest frame — every bone
  (arm and leg segments alike) is elongated along its own local -Z from 0
  to `-boneLength` regardless of real body direction — which is why the
  earlier translation-only FK test collapsed every limb into a blob: real
  per-bone rotation is structurally required, and it is genuinely absent
  from the model header/bone table, not just unfound. Four candidate
  sources were checked and refuted: `flagA`/`flagB` (only `{0,1}`, no
  per-sibling variation), header scalars `h[0]`/`h[1]`/`h[8]` (single
  per-model values, can't carry N per-bone rotations), and an unreferenced
  "marker" vertex at root/solo bones that looked promising but a
  corpus-wide census (417 markers, 830 models) found inconsistent
  magnitudes and exact-value repeats across unrelated packages, refuting it
  as real per-character data (see `pe-actor-root-marker-vertex` in
  `docs/parasiteeve/TODO.md`). Shipped a generalizable heuristic
  hierarchy-aware bind-pose assembly (`tools/shared/psx-actor-pose.ts`)
  replacing the old flat per-bone-index exploded grid: real bone hierarchy
  + real per-bone lengths, plus a geometric direction heuristic (mirrored
  equal-length sibling pairs split at a blended angle off the parent's
  inherited direction, not a full 90°; unpaired 3+-way branches fan at
  golden-angle spacing, not even 360/N — see
  `canonical-local-rest-frame-tests-rotation-necessity.md` and
  `golden-angle-sibling-fan-avoids-axis-collision.md`). Verified via a
  corpus-wide anchor-collision census (0/0 across 830 models x all bone
  pairs) and Playwright visual inspection of 4 models — a real readability
  improvement (connected, symmetric, head-torso-limb silhouette), a display
  heuristic, not a decoded pose.

  > **Superseded (2026-09-01, later session, `ghidra-disasm` trace) —
  > real rotation SOLVED, task `pe-actor-anim-tracks` closed.** The
  > missing rotation data lives in chunk3 slot 3's animation-clip
  > resource, whose byte grammar a prior session's structural-only
  > hypothesis (a flat 16-byte header + raw `s16` per-frame curves) never
  > matched. A `ghidra-disasm` trace of `SLUS_006.62` found the real
  > mechanism: `FUN_80039b74` dispatches on the clip header's low 2 bits
  > to an 8-bit-rotation-sample decoder (`FUN_80039d24`, 7,367/9,042
  > clips) or a 16-bit one (`FUN_80039ed4`, 1,675/9,042 — genuinely live,
  > not dead code as first suspected); each per-bone/per-frame track
  > (translation and every rotation) is independently constant-or-varying
  > via its own leading `u16` marker; angles feed a hand-rolled fixed-point
  > Euler->3x3-matrix builder (`FUN_80079754`, sine/cosine table
  > `DAT_800966ec`) and PSX-GTE-opcode (`ldclmv`/`nRTIR`/`stclmv`)
  > hierarchical FK composition (`FUN_8003a088`). The animation
  > directory's `flags >>> 24` field is the owning model's own directory
  > `id` (0 exceptions/821 matched groups), and `clip.boneCountByte`
  > always exactly equals that model's real bone count, including a
  > confirmed-intentional `+1` (an always-inert placeholder bone record,
  > matching the model format's own `h[1]=boneCount+1` convention — see
  > `genuine-off-by-one-loop-matches-placeholder-record-convention.md`,
  > sourced from here). **Verified two ways with no external oracle
  > needed**: byte-exact whole-corpus consumption (9,042/9,042 clips, 0
  > remainder, both rotation-width variants) and a novel **FK
  > distance-preservation** check — a parent-child bone's world-space
  > distance must equal its own already-confirmed static length iff the
  > byte grammar + matrix formula + FK composition are ALL correct
  > simultaneously (rotation preserves length) — 0 exceptions across
  > 106,444 sampled bone/frame pairs, max error ~2.27e-13; this also
  > independently resolved the tracing agent's own explicitly-flagged
  > lowest-confidence line (a matrix term's sign) via a 2,000-trial
  > orthonormality sweep before the corpus check even ran. See
  > `fk-distance-preservation-verifies-rotation-decode.md` (sourced from
  > here). **Shipped**: `tools/shared/psx-actor-animation.ts` (new
  > decoder) and an extended `tools/shared/psx-actor-model-gltf.ts` (real
  > `options.pose`/`options.skin` — glTF skin + `inverseBindMatrices` +
  > named `AnimationClip`s, rigid one-bone-per-vertex joints), wired into
  > `tools/parasiteeve/actor-model-assets.ts`. Of 830 models: **721** get
  > the real decoded bind pose (superseding the heuristic for those —
  > `psx-actor-pose.ts` remains the fallback for the rest, unchanged), and
  > **715** additionally ship real skeletal `AnimationClip`s (`fps=30` is
  > a display estimate, not decoded data — the format has no playback-rate
  > field). This pass also fixed two real, previously-undetected
  > `@gltf-transform/cli` bugs surfaced by the new skin export: a
  > degenerate (zero-area) triangle's normal falling back to invalid
  > `[0,0,0]` instead of a unit vector (this also fixed a PRE-EXISTING
  > defect affecting 517/393,917 triangles across 71/830 models, present
  > since the original 136-model shipment), and `SKIN_NO_COMMON_ROOT` on
  > the minority of models with more than one root bone (fixed via a
  > synthetic "armature" node parenting every root). Full-corpus
  > `@gltf-transform/cli validate`: 0 errors across all 714 checked
  > skeletal models. Still open: ~399 "group 0" clips whose
  > `modelId`/ownership scheme doesn't match the resolved 821-group
  > pattern, and 4 unidentified `u16` header fields — see
  > `docs/parasiteeve/TODO.md`.
  >
  > **Correction (2026-09-11) — track-index off-by-one, both numeric
  > oracles above are provably blind to it.** `localBoneTransforms` read
  > bone `i`'s rotation from track `i`, wrongly assuming (by analogy with
  > the model format's own confirmed convention) that the clip's
  > `+1`-extra track was TRAILING; it's LEADING — bone `i` needs track
  > `i+1`. Every bone got its own next sibling's real rotation. Neither
  > byte-exact consumption nor FK distance-preservation can detect this:
  > both are blind to *which* valid/length-preserving track gets read.
  > A prior session's own claimed Playwright visual check was false (see
  > `verify-escalation-artifacts-not-just-claims.md`, now generalized past
  > formal escalations to cover any agent's own unverified "I looked and
  > it's fine" claim); a real re-check found every skinned model rendering
  > as a collapsed clump + one rigid disconnected limb, present at the
  > rest pose itself. Root-caused by plotting the decoded skeleton as a
  > plain matplotlib wireframe (bypassing glTF/skin entirely) and
  > comparing two structurally-identical mirror-pair leg chains' rest
  > directions — one hung down normally, its twin pointed sideways/
  > forward. A tempting alternative hypothesis (a synthetic-armature-node
  > `JOINTS_0`/`skin.joints[]` index shift) was checked and refuted first,
  > both algebraically and by a numeric replica of three.js's own skinning
  > formula fed the real emitted glTF+bin bytes (diff 0.0000 at rest AND
  > mid-animation) — the glTF export code was never the bug. Fixed with
  > `frame.rotations[i+1]`; a new corpus-wide "mirror-pair direction
  > plausibility" regression test (645 real pairs, structurally detected,
  > no hardcoded bone indices) went from median cosine 0.73/min -0.35
  > (buggy) to 0.996/min 0.46 (fixed), and 5 models re-screenshotted across
  > every real clip now show coherent standing figures. See
  > `length-invariant-blind-to-track-index-misalignment.md`.
  >
  > **Correction (2026-09-11, later same-day session) — the "coherent
  > standing figures" claim directly above was only PARTIALLY true; a
  > SECOND, independent bug remained, now escalated to
  > `re-codebreaker`.** An independent re-verification (same method: real
  > headless-Chromium Playwright against the real offline viewer) found
  > the lower body (hip/leg chain) renders coherently, but everything
  > above roughly waist height explodes into a mass of disconnected,
  > wildly-rotated fragments — a "totem pole" effect — across every
  > model checked. Root cause: 775/830 models (93%) have MORE THAN ONE
  > bone with `parentIndex===-1` (up to 14 in one model, not a rare edge
  > case), and the pre-existing composition code treated every one of
  > them as an independent world-orientation root, which is wrong for
  > every root beyond the first (always bone-table index 0, confirmed
  > 830/830). The already-shipped verification oracles are provably
  > blind to this class of bug: FK distance-preservation only checks
  > parent-child DISTANCE, which any rotation (including a wrong one)
  > preserves; the mirror-pair-cosine test only checks RELATIVE agreement
  > between siblings, and a whole subtree corrupted uniformly (both
  > mirrored halves moved wrong together) still "agrees with itself" —
  > see the new lesson
  > `statistical-proxy-blind-to-whole-body-visual-defect.md`, sourced
  > from here. A principled partial fix (secondary roots compose their
  > rotation onto the true root's world rotation, origin pinned to the
  > true root's origin) was implemented and shipped as a non-regressing
  > improvement, but is mathematically PROVEN insufficient in general: a
  > rigid rotation about a fixed point cannot change any point's
  > distance from that point, only its direction, so a corpus-wide check
  > (277 multi-root models) found the old (independent-root) and new
  > (composed) formulas give IDENTICAL "how far does the subtree reach"
  > percentiles to floating-point precision (median 163.8, p90 317.5,
  > max 1275.9 units) — confirmed both mathematically and by real,
  > visually-unchanged screenshots for most affected models. Three
  > structural leads for a real per-root attachment/offset field
  > (bone-table `flagA`/`flagB`, model header scalars, an unreferenced
  > "marker" vertex at root/solo bones) were already checked and refuted
  > by an earlier session. This satisfied the escalation contract's bar
  > (2+ genuinely different failed hypotheses, each with a distinct
  > documented reason) and was handed to `re-codebreaker` to trace
  > `FUN_8003a088` (and its caller/setup code) at the instruction level
  > for the real multi-root rule.
  >
  > **Correction (2026-09-11, escalation result, independently
  > re-verified) — SOLVED, and a second bug found and fixed along the
  > way.** `FUN_8003a088` never reads `parentPlus1` at all: it executes a
  > **bone-hierarchy stack program**, a byte stream living inside the
  > model resource (located by tracing `FUN_8003d050`'s pointer chain,
  > sitting between a per-row 16-byte array and the UV tail). Grammar:
  > `-1` push the current GTE matrix, `-2` pop, else compose hierarchy
  > ROW N onto the current matrix. This also identifies `h[12]` as the
  > program's own byte length. `parentPlus1` is a hierarchy ROW index,
  > not a "no parent" sentinel — row 0 is the record at `model+0x1c` that
  > `tryParseModel` had always skipped as "inert"; it's a REAL, sometimes
  > per-frame-ANIMATED node (non-identity in 599 clips, animated in
  > 283/5,928 multi-frame clips) carrying the clip's decoded translation
  > AND its own rotation track 0, which the pipeline had been discarding.
  > Every bone (not just a lucky first one) composes against its own
  > parent row — no special-casing needed once row 0 is real. Verified:
  > decoding the program and reading its implied parent reproduces the
  > stored `parentPlus1` byte for **15,641/15,641 rows across 830/830
  > models, 0 deviations**, and an independent from-scratch replica of
  > the stack machine (driven by raw program bytes, not `parentIndex`)
  > matches the shipped `composeWorldTransforms` to `<1e-9` on all 721
  > rest-posed models — shipped as a mutation-tested regression test
  > (reintroducing the old bug, or the escalation's own briefly-shipped
  > H_fix1 patch, both fail it by orders of magnitude). The escalation
  > ALSO caught that its own H_fix1 predecessor was a live, shipped
  > regression — byte-diffing the assets on disk against a from-scratch
  > H_fix1 replica matched at `maxErr=0.000`, i.e. the "shattered mass"
  > screenshots were H_fix1's own output, not the original bug.
  >
  > **A second, genuinely separate bug, correctly diagnosed by the
  > escalation but fixed in an independent same-day follow-up**: PSX is
  > Y-down, glTF/three.js is Y-up, and nothing flipped it — this alone
  > reproduced the "totem pole" appearance in a fresh Y-flip-free replot
  > of the corrected geometry. The follow-up fix applies one Y-axis flip
  > at export time only (`tools/shared/psx-actor-model-gltf.ts`, never
  > touching the fully-tested PSX-native `psx-actor-animation.ts` core):
  > a raw point negates trivially, but a rotation matrix needs
  > conjugation by the reflection `F=diag(1,-1,1)` (`R'=F·R·F`) to stay a
  > proper rotation (determinant +1, a valid glTF quaternion) — plain
  > component negation breaks this. Conjugating every LOCAL transform
  > once lets the existing (unmodified) parent-child composition produce
  > correctly Y-up WORLD transforms automatically, since composing
  > already-conjugated locals telescopes exactly:
  > `F·(P·L)·F = (F·P·F)·(F·L·F)` — verified numerically (0 deviation,
  > random rotations) before trusting it on real data. Both fixes
  > independently re-verified end-to-end, not just the escalation's own
  > claims taken at face value (see `verify-escalation-artifacts-not-
  > just-claims.md`): a from-scratch triangle-mesh plot of the shipped
  > static POSITION buffer, a live extraction of three.js's own computed
  > SKINNED vertex positions (matching the static bake to float32 noise,
  > ruling out a skinning-side bug), and fresh Playwright screenshots
  > (not reused from the escalation) of 6+ models at rest and mid-clip —
  > all now coherent, right-side-up standing figures/creatures. `npm
  > test` still 78/78 (the native-space tests are unaffected by the
  > export-layer fix, as intended);
  > `@gltf-transform/cli validate` 0 errors on the rebuilt corpus. Both
  > `pe-actor-multiroot-attach` and `pe-actor-gltf-y-up` are now closed
  > in `docs/parasiteeve/TODO.md`; a small residual cosmetic gap (a
  > floating shoe/boot fragment on a few models, unrelated to either bug,
  > present identically before and after both fixes) is tracked as
  > `pe-actor-model-shoe-gap`.
- **Chunk3 slot 8 resolves to `AKAO`, not a new audio subsystem.** 8-byte
  cue records (`u16 zero; u8 zero; u8 gateFlags; u16 soundId; u16
  zero-or-flag`) index a second static table at `SLUS_006.62+0x83980` (252
  ascending `u16` sector deltas from base sector `0x8b0`); 6/6 sampled
  `soundId`s resolve to `PE.IMG` sectors starting with literal `AKAO` — the
  same Squaresoft in-house sequence format already flagged for this
  project's separate audio-extraction agent. Not decoded further here (out
  of this agent's scope by design). Also confirmed: `PE.IMG[0x458000,
  0x1178800)` (13.7 MB) is a dense bank of 200+ individually-tagged `AKAO`
  files — the main music/SFX bank location.
- **Prerendered backgrounds — SOLVED positively (2026-09-01), overturning a
  twice-reaffirmed negative.** An initial `ghidra-disasm` trace exhaustively
  enumerated all 15 real callers of the two raw-CD-read primitives (actor-
  package loader, face/icon variant loaders, the boot splash state machine,
  FMV setup, a generic UI/dialog loader, a name-randomizer, the AKAO
  audio-cue streamer) and correctly found none room-keyed, and a
  whole-executable `MDEC` string/register search correctly found nothing —
  both real, both still true. But the conclusion drawn from them ("no
  prerendered background asset exists at all") was wrong: this game
  composites its static-camera room backgrounds at **runtime**, from data
  already resident as part of the ordinary actor-package load, with no
  fresh disc read at all — a mechanism a disc-I/O-scoped census is
  structurally blind to (see `disc-io-census-blind-to-already-loaded-data-
  consumer.md`). The real mechanism is chunk3 slot 6's "scene blob": a
  trigger/zone array whose per-tile "source B" records carry an
  already-packed tpage-shaped word (`tx`/`ty`/`clut`/`u`/`v`), spliced
  directly as `SPRT_16`+`DR_TPAGE` GPU primitives sampling chunk1's own
  VRAM x=768/832 pages (`tools/shared/psx-tile-scene.ts`,
  `tools/parasiteeve/actor-background-scenes.ts`). This was **twice**
  independently re-investigated and reaffirmed as "chunk1 confirmed
  unused" by two further `ghidra-disasm` escalations (an exhaustive
  tpage-bitfield-*construction* census, then an exhaustive 2D-blit-
  primitive/`LoadImage`/`StoreImage`/`MoveImage` census) — both real,
  careful, and both false negatives, because neither could ever find a
  consumer that reads an already-packed value straight out of a data
  record with no construction step (see
  `data-table-stores-prepacked-value-code-census-misses-it.md`). What
  finally broke the tie was not a fourth code census but **rendering the
  actual corpus-wide visual output**: 414/414 packages produce non-empty,
  unmistakably real, thematically-coherent PSX background art (a NYC
  street with a marked ambulance, an industrial "ROOMS" corridor, a
  warehouse interior, an art-deco Christmas ballroom, a hand-lettered "PE"
  title card) — 362,647 tile records decode with 0 parse errors, 29.5% of
  them referencing chunk1's own pages. Shipped:
  `public/assets/parasiteeve/psx/backgrounds/` (414 PNGs). The earlier
  chunk3-slot-6 "background-image-directory" hypothesis (footer bytes
  decoding to plausible 320x240/320x224 dimensions, matching a community
  forum's "folder 6 = background" claim) had already correctly named the
  right mechanism (camera/trigger/tile-scatter) but stopped the trace one
  hop short — see `domain-refuted-by-shape-not-values.md` for the
  "dimensions are really viewport constants" sub-finding, which remains
  correct on its own narrow terms.

  > **Follow-up (2026-09-02) — two real bugs found and fixed, room-split
  > rendering shipped.** The initial pass's tile-delta sign convention
  > (two's-complement) was WRONG — the fields are **unsigned** — and its
  > renderer combined every simultaneously-"active" trigger in a package
  > into one canvas with no per-trigger `baseX`/`baseY` offset applied,
  > which together produced a visible artifact on some packages (two
  > disconnected/overlapping scenes in one image, matching a real in-game
  > observation of one room shown from two distinct fixed camera angles).
  > Both were fixed via a combination of corpus-wide data analysis (every
  > active trigger's own raw per-record minimum is exactly 0, 2078/2078
  > zero exceptions, plus a literal contiguous full-width background
  > raster row that a signed reading would tear apart at the 512 boundary
  > — see `corpus-wide-zero-minimum-plus-contiguous-row-confirms-unsigned-
  > field.md`) and a `ghidra-disasm` instruction-level trace of
  > `FUN_80067a78`/`FUN_80067294` (and the parallel walker
  > `FUN_800677fc`/`FUN_80066f60`) that confirmed all three: unsigned
  > field decode (`srl`, never `sra`), real `baseX+delta` placement code,
  > and — the actual root cause of the visual artifact — a trigger record's
  > `+0x24` byte is a genuine separate gate compared against a live global
  > (`0x800bcffd`), independent of the `flags` active bit, selecting which
  > one of several simultaneously-"active" triggers is the game's
  > currently-showing camera angle; triggers sharing that byte's value are
  > meant to composite together (one primary full-canvas background trigger
  > plus several `baseX`/`baseY`-anchored decorative overlay triggers), but
  > different values are mutually-exclusive alternative angles for the same
  > room — see `active-flag-plus-runtime-discriminator-means-mutually-
  > exclusive-not-combined.md`. Fixed renderer now groups triggers by this
  > discriminator and ships **509 room-background PNGs across 414
  > packages** (74 packages have 2+ room/camera angles) instead of one
  > combined-and-broken image per package —
  > `public/assets/parasiteeve/psx/backgrounds/actor<NNN>_scene[_<room>].png`.
  > Also fixed a real `always-full-run-manifest-merge-accumulates-stale-
  > entries.md` instance this triggered (a package's output filename
  > *count* can now change between runs, orphaning the old unsuffixed
  > manifest entry — fixed with a prune-then-upsert scoped to the
  > `backgrounds` manifest category). See `docs/parasiteeve/psx/data-
  > structure.md` § "Prerendered backgrounds" (the 2026-09-02 correction
  > blocks) for the full evidence chain.

  > **Follow-up (2026-09-11) — a corpus-wide pixel census found 42/509
  > images >=95% solid black (6 at 100%); both real causes found and
  > fixed, one residual class root-caused but not further fixed.**
  > (1) `actor-background-scenes.ts` filled unpainted canvas area with
  > OPAQUE BLACK instead of `alpha=0`, on the reasoning that transparency
  > would overclaim about the game's own compositing — backwards in
  > practice, since opaque black is itself the false claim ("this pixel
  > really is black"). Fixed to default transparent, `alpha=255` only
  > where a real tile is painted; the viewer already respects PNG alpha
  > correctly (plain `ctx.drawImage`, no canvas pre-fill, CSS-toggled
  > background behind it), no viewer change needed. See
  > `opaque-fill-for-unpainted-region-is-a-false-visual-claim.md`.
  > (2) The actual root cause of all 6 100%-black images: `psx-tile-
  > scene.ts`'s trigger `tileCount` field is an ALLOCATED-CAPACITY value,
  > not a real-content length — a corpus-wide census (306,620 tile
  > records, 2,078 active triggers, 0 exceptions) found every fully-zero
  > 12-byte tile record (`x=y=otIdx=tx=ty=clut=u=v=0` all at once, not
  > just one suspicious field) sits in an unbroken run ending at
  > `tileCount-1`, never before a real tile — the same "+1 trailing
  > placeholder" convention as this project's own model bone table, just
  > with a variable-length run instead of a fixed `+1`. The old code
  > painted hundreds of fake `(x=0,y=0)`-placed pure-black tiles per
  > affected trigger AND fed `(0,0)` into the room's bounding-box
  > computation, inflating the canvas around a real-but-tiny content
  > region. Fixed by skipping fully-zero tile records. See
  > `declared-record-count-is-allocated-capacity-trailing-zero-run-is-padding.md`.
  > Post-fix: 0/509 images >=95% opaque black. (3) A residual class — 4
  > packages (`actor346`/`359`/`381`/`430`) plus one room of `actor428` —
  > still render their real (non-placeholder) tiles as solid black.
  > Traced directly against raw `PE.IMG` bytes (not guessed): their CLUT
  > resolves to the CORRECT VRAM address inside their own chunk2 upload
  > rectangle, but the raw on-disc source bytes there are genuinely
  > near-blank (2/16,384 nonzero bytes for the worst cases vs.
  > 187-255/256 nonzero for a healthy room's identical-shaped CLUT block,
  > confirmed by direct comparison against `actor000`/`actor004`) — not a
  > decode bug, since the plumbing is provably correct against the
  > healthy corpus. Best explanation (not code-traced this session): a
  > shared/underlay VRAM dependency this per-package static extraction
  > can't reconstruct, the same class of gap as the already-documented
  > "bust card" (`pe-actor-bust-card-pixel-format`) item. Tracked as
  > `pe-tile-scene-blank-clut-rooms` in `docs/parasiteeve/TODO.md`.
- **Model-signature check was overfit to one reference instance — since
  fixed and shipped.** The chunk3 slot-2 model detection gate
  (`h[12]===31 && h[15]===1 && h[17]===255`) originally capped the shipped
  corpus at 136/438 entries. `h[12]` was confirmed to be real per-model
  data (likely a bone/part count), not a magic constant — the original
  signature only worked because its one reference instance happened to
  have `h[12]==31`. See `model-signature-field-mistaken-for-magic-
  constant.md`. Fixed and shipped: dropping `h[12]` from the signature
  ships **830/830** models (up from 136), re-verified structurally and via
  `@gltf-transform/cli validate` (0 errors) before shipping.
- **The shared status-UI VRAM bank ("bust portrait" system) — mechanism
  fully traced, but not a per-model texture gap.** ~205/830 shipped models
  reference VRAM x=704 (a second bank, x=960, is a sibling), which their own
  actor-package chunk1/chunk2 never uploads to. A `ghidra-disasm` escalation
  traced the real code-level mechanism byte-exact: a small, self-contained
  status/reveal UI subsystem (`FUN_8006c5bc`/`FUN_8006becc`/`FUN_8006c1cc`
  in `SLUS_006.62`) indexes the already-known shared 336-entry resource
  table (`SLUS_006.62+0x838d8`) via a runtime UI face-slot selector
  (`DAT_800b0ce4`, range 1-8) that has **no relationship to package
  identity at all** — confirmed by a full xref sweep that the generic
  per-package loader never calls into this subsystem. Bank B (x=960 +
  shared CLUT, table index 17) decodes byte-exact against this project's
  own slot-9 invariant (3/3 records, zero deviation, genuinely-zero
  padding) — but the escalation's claim that Bank A (x=704, table indices
  39-44, the bank that actually matters for the 205 models) also decodes as
  plain slot-9 records did **not** survive independent re-verification: only
  each resource's first record comes close (still off by 32 bytes), and the
  "padding" bytes are non-zero and structured, meaning Bank A is a real but
  different, still-undecoded 20-byte record format — a fresh instance of
  `verify-escalation-artifacts-not-just-claims.md` (re-derive from the
  project's own already-proven invariant, don't trust a "decisive"
  byte-level claim at face value). Separately, a corpus census of the 205
  "affected models" found them **structurally byte-identical** (15
  vertices, 2 boxy root bones, 10 quads, 0 tris — one shared "bust card"
  mesh template stamped into 205 different packages, not 205 distinct
  items), which combined with the UI-state-driven bank selection means
  there is no deterministic per-model "correct" texture to recover here
  even once Bank A's format is decoded. No texture-bake fix was shipped (an
  implementation was built, verified to silently no-op because the
  project's own invariant guard correctly rejected the unverified data, and
  reverted rather than ship a fabricated/misleading fill). See
  `docs/parasiteeve/psx/data-structure.md` § "The shared status-UI VRAM
  bank" and `tools/shared/psx-actor-vram.ts` (`applySharedUiResource`,
  `readSharedTable` — both verified and kept, unwired).

## Open

See `docs/parasiteeve/TODO.md` for the current list (bone-table/model-header
unknown fields, chunk3 slots 0/1/10/11 fully undecoded, slot 4/5 structurally
identified but not byte-decoded, animation-track rotation decode, the Bank A
"bust card" bank's own still-undecoded 20-byte pixel-record format
(`pe-actor-bust-card-pixel-format` — narrower than before: mechanism is
solved, only the byte format remains, and decoding it would only enable a
"pick one representative face" fill, not a per-model fix), and a few open
sub-details of the now-solved tile-scatter background system itself — sign
convention cross-check, camera-scroll `baseX`/`baseY` not applied,
multi-active-trigger semantics).

# parasiteeve2 — Parasite Eve II (PSX)

**Project root:** `~/Development/parasite` (same repo as PE1 above — a
**different, unrelated codebase**; do not assume any format transfers from
PE1 without independent verification)
**Game/platform id:** `parasiteeve2` / `psx` (disc1 `SLUS_010.42`, disc2
`SLUS_010.55` — the two discs boot **different** executable filenames,
unlike PE1's shared `SLUS_006.62`)

Square, 2000. Same PSY-Q BIOS toolchain source-control tags as PE1
(`makoto`/`noda` `$Id:` strings) — evidence of a shared SDK, not a shared
game engine. First-pass exploratory session; docs:
`docs/parasiteeve2/psx/data-structure.md`, `docs/parasiteeve2/TODO.md`,
`docs/parasiteeve2/plan.md`.

## Prior art — an active community decompilation project

[`GabeRealB/parasite-eve-2-decomp`](https://github.com/GabeRealB/parasite-eve-2-decomp)
(MIT, active — pushed the same day this session ran) is a real matching
decompilation of `SLUS_010.42` with extensive `doc/*.md` format
documentation (container/chunk framing, LZSS, TMD 3D models, `.spk` audio,
`STAGE0.HED` streaming lists) and a working Python extractor
(`tools/peassets/`). Existence verified via the GitHub API before trusting
it. Every specific claim used from it was independently re-verified against
this session's own real disc bytes — full field-by-field agreement on
`STAGE0.HED`'s 3-entry streaming list (movie ids 100/101, frame-count hint
`0x73a`, audio stream byte offset `0x87C000`, all zero-deviation), plus one
real correction found and documented (a chunk-header field's stated unit —
see `format-doc-prose-may-describe-converted-value-not-raw-field.md`).

PE2 does **not** use the AKAO sequence format PE1 does — confirmed both by
its absence from vgmtrans's own cross-title `AkaoPs1Version` history (which
otherwise brackets PE2's release date exactly, `VERSION_2`="Parasite Eve"
then `VERSION_3_0`="Another Mind") and by real `hSPK` magic bytes in
`STAGE0.CDF`'s first chunk — a separate, unrelated in-house sound-bank
format.

## Solved

- **`STAGE0.HED`/`STAGE0.CDF` chunk container** — 16-byte chunk header
  (`type`/`end_flag`/`sector_len`/`chunk_size`-in-sectors/`load_addr`/pad),
  a 3-slot movie/audio streaming list, and an ascending file-boundary table,
  all confirmed byte-exact against real disc data.
- **`INTER0.STR`/`INTER1.STR` cutscene movies** — confirmed byte-identical
  container to PE1's own FMV corpus (`tools/shared/psx-str-xa.ts` reused
  **unmodified**, verified not assumed). PE2 bundles an entire disc's
  cutscenes into one file and seeks to a per-cutscene sector offset at
  runtime (rather than PE1's one-file-per-cutscene convention) — heuristic
  frame-boundary segmentation (`tools/parasiteeve2/movie-assets.ts`,
  reproducing the community project's own documented fallback policy)
  found 21+18 real segments across both discs and independently landed on
  the identical 18,620-sector title-FMV boundary the community doc cites,
  with no prior knowledge of that number. Shipped end-to-end: 39/39
  segments transcoded via ffmpeg, ~26.3 minutes combined runtime, zero
  failures. `npm run extract-data -- --game parasiteeve2 --platform psx`
  registered and green; PE1's own pipeline re-run and confirmed
  regression-free.
- **`.pe2pkg` room-package LZSS + TMD 3D models** (later session). The
  community project (`GabeRealB/parasite-eve-2-decomp`) had progressed far
  past the earlier session's read by the time this session re-cloned it
  fresh — a complete, documented LZSS decoder (not just "algorithm shape
  confirmed") and **all 23** TMD draw families mapped (not "2 of 23") — see
  `tracker-prose-is-not-evidence.md`'s external-reference-project variant,
  sourced from here. LZSS ported to `tools/shared/psx-pe2-lzss.ts` and
  verified **448/448 byte-exact, 0 mismatches** against a real run of that
  project's own `extract.py` invoked directly against this project's actual
  disc files (its CLI's file arguments map 1:1 onto this project's own
  `dumpsxiso` layout — no adaptation needed); this project's own
  `tools/parasiteeve2/pe2-stage-container.ts` extends the already-confirmed
  chunk-header layout into a full `STAGE0`/`STAGEn` folder+file+chunk
  walker. TMD geometry ported to `tools/parasiteeve2/pe2-tmd.ts` (the
  source-backed `TmdSource`-location path only, not the opcode-walk
  fallback) and confirmed via the reference project's own exactly-cited
  per-model counts (Kyle's body: 300 verts / 20 parts / 398 faces, exact
  match) plus real headless-Chromium screenshots (via this repo's own
  `tools/viewer/`) of 3 structurally distinct models — a human female
  character, an armoured winged creature, a hunched clawed monster — all
  rendering as coherent, correctly-proportioned standing figures, not
  collapsed/exploded/inverted geometry. Ships 598 static (rest-pose,
  untextured) glTF meshes as `type: "model"` manifest entries. A real
  Python-`//`-to-JS-`/` porting bug (a fractional vertex/normal count from
  an unfloored pointer-gap division) was caught via a non-integer debug
  print before it could silently misalign array reads — see
  `python-floor-division-port-to-js-silent-fraction.md`, sourced from here.
- **`.pe2pkg` TMD textures** (later session) — every textured primitive
  carries its own absolute `tpage`/`clut` fields directly in the geometry
  stream (no offline CLUT-row guessing needed, unlike PE1's 2D UI
  textures); PE1's `psx-actor-vram.ts` GPU-hardware helpers reused
  unmodified. 568/598 models textured, verified via real Playwright
  screenshots (6 structurally distinct, correctly-textured characters/NPCs/
  monsters) — see `confirmed-generic-mechanism-may-not-apply-to-this-
  instance.md` for a real false-lead corrected the same session (a
  disassembly-confirmed `Gp_PumpTmdStream` tpage-bias override doesn't
  apply to Kyle's own body mesh, only some other object).
- **`.spk`/`hSPK` audio + the `hONE` SndScript event grammar** (later
  session). `tools/parasiteeve2/pe2-spk.ts` ports the community project's
  own `spk_codec.py` (header/note-table parse + PSX SPU-ADPCM decode),
  verified byte-exact (0/48,020 PCM sample diffs) against that reference
  decoder's real output. Went a step past the reference project itself:
  the `hONE` SndScript **event-stream grammar** — which that project's own
  doc explicitly still calls unsolved (`INCLUDE_ASM`) — was derived
  first-hand from that same project's `src/main/sndscript.c`, which
  turned out to be **already fully decompiled** despite the stale doc
  claim (grep-confirmed; a new, distinct "external reference project's own
  docs can lag its own current source" pitfall, see
  `reference-project-doc-claims-stale-vs-own-current-source.md`, sourced
  from here). `tools/parasiteeve2/pe2-hone.ts` decodes the tag grammar
  (`oneV`/`oneC`/`Wait`/`Loop`/`endL`/`endC`, `oneA`/`oneE` side-tables) —
  no external oracle exists for this sub-format, so verification is
  corpus-wide self-consistency (100% of one hand-audited program's bytes
  accounted for; 98.5% of 3,550 tracks corpus-wide walk cleanly to a real
  `endC` with 0 unrecognized opcodes across all 831 real banks on both
  discs). A real bug in this session's own directory-length auto-detector
  (byte-granularity tag scan instead of word-aligned) is folded into
  `terminator-scan-must-be-record-aligned.md`'s scope. Ships 472 unique
  banks / 2,932 real, non-degenerate PCM16 WAV samples; full timed/
  sequenced playback not wired up (see TODO `pe2-spk-audio`).
- **MDEC "BS v2" still images (`INIT.BS` + room-background chunks)**
  (later session) — no MDEC pixel decoder existed anywhere in this
  account's seer ecosystem before this (every sibling project's own PSX
  `.STR` pipeline, including this one's own PE1, delegates to ffmpeg
  instead). `tools/shared/psx-mdec-bs.ts` is a from-scratch port of the
  community project's complete `bs_codec.py` (MPEG-1 AC VLC trie, PSX
  fixed-point IDCT, chroma upsample) — verified **pixel-exact** (0/230,400
  byte diffs) against that reference decoder's own output on `INIT.BS`,
  which decodes to a fully legible "Published by Square Electronic Arts
  L.L.C." boot logo. Applied with zero changes to the same chunk type
  (`0x5`) inside the already-solved `.pe2pkg` stage container: 1,759
  unique room-background chunks (of 2,330 found, deduped by SHA-1 across
  the cross-disc `STAGE3.CDF` duplicate — see §1), **100% decoding all
  300/300 macroblocks** at a uniform 320x240, rendering real, coherent,
  recognizable PE2 environment art (several captioned "Now Loading").
  1,760 PNGs shipped.

## Open

The **~35 non-`TmdSource`-backed** TMD model streams (reachable only via
runtime code), a small (~4-model) texture residual, `.spk` **sequenced
playback** (samples + event grammar decoded, not wired to real timing —
plus a specific, well-characterized 1.5%-of-tracks `oneC`-then-`Loop`
anomaly, open), which room/scene each MDEC background belongs to (no
per-chunk name decoded), the real per-cutscene `interOffset` catalog
(current movie segmentation is heuristic), and two unresolved anomalies:
`PE_DISK.01`/`.02` (byte-identical across discs, high-entropy, likely a
disc-authenticity token) and `DUMMY.DMY` (see
`file-named-dummy-may-hold-real-leftover-content.md` — looks like real
leftover MDEC-bitstream-shaped content, not padding — the now-existing
`psx-mdec-bs.ts` decoder is a real, unattempted next step for it, though
its own header claims a non-standard 256x176 resolution). **TMD skeletal
animation is now SOLVED end-to-end and shipped** (a follow-up session):
`GpPackedSvec`'s bit layout (`vx:11,vy:10,vz:11`, `<<3` scale) was
independently CONFIRMED — not just structurally consistent — by
hand-disassembling the real, unmodified `Gp_AnimBlendPacked` MIPS machine
code straight out of this project's own decoded `gameplay` overlay (no
capstone/r2 available in this sandbox, so a from-scratch minimal MIPS32
decoder was written for exactly the needed opcodes), and the
`RotMatrix_gte` Euler->matrix formula was independently confirmed against
Sony's own official PsyQ `Libref.pdf` SDK documentation after locating it
as a stock, statically-linked `libgte/rmat_01` library routine (not
project-specific code) via the decomp project's own `main.yaml` — see
`stock-sdk-routine-official-docs-outrank-disassembly.md`, sourced from
here. Real glTF skinning (rigid single-bone weights, a real
`inverseBindMatrices` palette from the confirmed bind-pose FK
composition, real `AnimationClip`s) shipped for Kyle's body
(`pe2_kyle_body_animated`, 34 real clips,
`tools/parasiteeve2/pe2-anim-gltf.ts`), verified via real headless-Chromium
Playwright screenshots of the actual shipped asset across **three**
clips in the actual production viewer (two independently-distinct
dynamic running gaits plus a stable, correctly-near-motionless static
idle control) — deliberately going past `@gltf-transform/cli validate`
(0 errors/warnings) and the FK-distance-preservation check (correctly
treated as a known-weak oracle here, since orthonormal rotations trivially
preserve parent-child distance regardless of correctness). Coordinate
handedness used an algebraically-derived per-bone-local conjugation
(`flipRT`) rather than a scene wrapper node, after the wrapper-node
approach tripped a real `NODE_SKINNED_MESH_NON_ROOT` glTF-spec violation
caught by the validator. **Extended (2026-09-13, same-day follow-up
session) to 5 more actors — pure asset-identification, zero new decode
work**: a brute-force sweep grouping every unique `.pe2pkg` body by its
own `loadAddr` and cross-checking against all 8 `Gp_AnimBlkTbl` entries
found real, validating animation blocks in exactly one more RAM slot
besides Kyle's dedicated one (`0x80161e20`, the generic "actor slot 3") —
resolving, via this project's own already-shipped static renders, to
**Ben** (Kyle's dog companion, a 19-bone quadruped, id `800200`) and
**Aya Brea** (her PE2 model, 19-bone humanoid, id `800300`), plus 3 more
Kyle outfit variants (`id800102`-`104`, visually identical to his
default body but independently-decoded content with their own texture
page and `GpAnimSet` table). A 32-package weapon-pickup single-bone
spin/bob animation family was also found at a third slot
(`0x8011d1c0`) but not shipped (not a skeletal character). Verified via
the SAME bar as the original Kyle pass — `@gltf-transform/cli validate`
(0 errors on all 5), a real-disc structural regression test
(`tools/parasiteeve2/__tests__/pe2-anim-actors.test.ts`), and real
Playwright screenshots of each shipped GLB across 3+ clips and multiple
timeline points per clip, confirming fully-connected, correctly
proportioned, genuinely-posing figures for all 5 (including a real
leap/pounce cycle for Ben, found via an FK-world-motion probe rather
than guessing clip indices) — deliberately not trusted on
self-report alone, per this project's own
`bind-pose-render-blind-to-joints-index-space-bug.md` lesson. 6 animated
actors / 204 total clips now ship. Open: the other ~592 shipped models
still ship static/rest-pose; `Gp_PlayerAnimBlkTbl` (a structurally
different 34-entry table pointing inside the gameplay overlay itself,
not per-character) remains untraced; one anonymous non-model file
(`id800100`) near Ben's own ids is uncharacterized. See
`docs/parasiteeve2/TODO.md` for the full tracked list.

# the3rdbirthday — The 3rd Birthday (PSP)

**Game/platform id:** `the3rdbirthday` / `psp` (USA/PLAYASiA)

Square Enix, 2011, a Parasite Eve spin-off (director Hajime Tabata, also
Crisis Core -FFVII-) — a **completely different codebase/engine** from
PE1/PE2 above, sharing only the franchise. No engine-sharing evidence
found with Crisis Core/Dissidia (no "Crystal Tools"/"White Engine"
reference located). First-pass exploratory session (2026-09-01); docs:
`docs/the3rdbirthday/psp/data-structure.md`, `docs/the3rdbirthday/TODO.md`.

**Container solved, no community tool needed to run it (but real community
prior art existed and was the unlock)**: almost the whole game lives in one
~1.28GB flat container, `3rd.pkg`, split into fixed 2048-byte segments and
addressed by a small (7,932-byte) companion file table, `3rd.fsd` — 8-byte
entries (`u32` segment-number-in-low-20-bits + a `groupId` in the high 12
bits of unconfirmed semantics; sizes derived by sorting entries by segment
start and diffing to the next one, terminated by a sentinel entry whose
segment number equals `pkgSize/2048` exactly). No QuickBMS script or
working extractor tool for this exact game was ever found (XeNTaX/ZenHax/
GitHub/TCRF/Models Resource all searched) — but a 2010-era XeNTaX forum
thread's own prose (`forum.xentax.com/viewtopic.php?f=10&t=5616`, recovered
via `WebSearch`'s indexed snippets after a direct `WebFetch` 403'd — see
`game-re-tooling/format-discovery.md`) gave the segment size and table
offset outright, letting this session independently re-derive and verify
the rest against real bytes with **zero disassembly of `eboot.bin`/
`boot.bin` needed**. 4 real content types identified in the 761-entry
corpus and shipped: standalone **PNG** (12, direct byte-copy), **PSMF**
movies (42 — Sony's PSP MPEG-PS-shaped container; ffmpeg's native
`mpegps` demuxer handles the H.264 video track with zero custom code, but
the ATRAC3+ audio, PSP `sceMpeg` `private_stream_1`, needed a manual
PES-walk — see below), **SEDBSSCF** (a Square Enix audio-database
container, 244 entries — 229/244, 93.9%, contain a findable embedded
`RIFF`/`WAVE` (`WAVEFORMATEXTENSIBLE`->ATRAC3+) chunk once the *full*
corpus was scanned, decoded via plain ffmpeg; an earlier 8-sample manual
probe found 0/8 and wrongly suggested "this sub-format is rare" — see
`small-sample-probe-undercounts-dominant-subformat.md`), and **`pack`**
(436 entries, 57% of the corpus — see below, **now solved and shipped for
231/436**). 6,207 textures (12 standalone PNGs + 6,195 `pack` texture-table
entries, see below) + 42 videos + 229 audio tracks + 231 pack models
shipped to `public/assets/the3rdbirthday/psp/`; SEDBSSCF's own header/
directory fields and the fsd table's `groupId` semantics remain open
(`docs/the3rdbirthday/TODO.md`).

**`pack` container geometry/texture format — SOLVED (2026-09-02, a
`re-codebreaker` escalation + independent re-verification)**. A follow-up
session's targeted escalation cracked the 57%-of-corpus `pack` container's
main-resource payload as **verbatim PSP GE (Graphics Engine) native vertex
array data** — the exact byte layout `sceGuDrawArray()` consumes directly,
addressed by a `f0c`-relative section-pointer table (`f0c` = the header's
own main-resource base) and self-describing per-block via a literal
`pspgu.h` vertex-type bitmask plus redundant stride/weight-count bytes.
The earlier "`0x7FFF`-dominated" characterization (a small-sample artifact,
see `small-sample-probe-undercounts-dominant-subformat.md`'s note on this
exact corpus) was itself the wrong read of a real hit: `0x7FFF` is the
literal weight-column value for `GU_WEIGHTS(1)` blocks, not a padding
sentinel. **231/436 packs / 5,584 blocks / 318,336 vertices / 106,112
triangles** decode with zero walk errors and zero self-check deviations
(each block independently stores its own weight-count/stride, which must
agree with the vertex-type-derived layout — a free, corpus-wide
cross-check). Textures came out as a side effect, and **both indexed
pixel formats are now fully solved** (a same-day follow-up corrected the
second one): `pixelFormat` is this game's own bit-depth tag, not the
literal `pspgu.h` `GU_PSM_*` enum a first pass assumed (that enum's real
`GU_PSM_T8` is 5, not 8) — `4` = 4bpp/16-color indexed ("T4", 6,131/6,488
descriptors), `8` = 8bpp/256-color indexed ("T8", 357/6,488, **previously
misidentified as `GU_PSM_DXT1`**). Both share one PSP-swizzled 16x8
block-interleave unswizzle helper and differ only in indices-per-byte and
CLUT size (64 vs. 1024 bytes = 16 vs. 256 RGBA8888 entries). The DXT1
misread came from pattern-matching pspgu's enum ordering rather than
checking the actual bytes; it was overturned by simple arithmetic (the
real per-texture payload length is exactly `width*height`, i.e. 1
byte/pixel — double what any DXT1/DXT3/DXT5 block-compressed reading could
produce) plus a render: decoding the same bytes as DXT-family formats
produced pure noise, while decoding as an 8-bit-indexed CLUT lookup
produced immediately recognizable sky/skyline/holiday-scene/creature-flesh
art. See `pixel-format-value-guessed-from-enum-not-confirmed.md`. A
generic, engine-agnostic
`tools/shared/psp-ge-vertex.ts` (derives vertex-type -> byte-layout from
the `pspgu.h` bitmask rather than a hardcoded per-title table — reusable by
*any* PSP title that uploads vertex buffers straight from a loaded file)
plus a `pack`-specific decoder/glTF exporter
(`tools/the3rdbirthday/pack-model.ts`/`pack-model-gltf.ts`) ship 231 real,
static (non-skinned) glTF models, all `@gltf-transform/cli`-validated
(11/11 sampled, 0 errors after fixing a real
`ACCESSOR_VECTOR3_NON_UNIT` issue from the s8-quantized normals — see
`discriminant-gated-field-convention-applied-unconditionally.md` for a
real implementation bug this pass caught and fixed: the dominant shapes'
`f0c + 0x34` geometry-pointer convention does **not** apply to the 14 rare
`count∈{2,4,7,11,34}` header shapes, and an ungated first pass produced 10
spurious garbage-geometry packs before a whole-corpus self-check test
caught it; both T4 and T8 textures now ship real decoded art for every
geometry-bearing pack). Still open: the block header's
`extraWords`/bone-matrix-palette payload, the 91 `count=8` effect/cutscene
packs (a different content class entirely — a float32 record stream +
`MDL\0`/`TEX\0`/`ANM\0` effect sub-chunks, unrelated to the geometry
format), and the 14 rare-header-shape packs.

**Cross-project mechanism transfer, verified not hypothetical**: the PSP
`sceMpeg`/`MpegDemux` `private_stream_1` ATRAC3+ PES-walk + minimal Sony
OMA/`"EA3"` header builder, originally built in `~/Development/valkyrie`
(`tools/shared/psp-atrac3p-audio.ts`, for Valkyrie Profile: Lenneth's PSP
remaster movies), was ported **verbatim** here and confirmed byte-exact on
this second, unrelated PSP title (a real sample walked to 692 frames of a
constant 744 bytes, zero remainder, decoding to real non-degenerate PCM).
Per `game-re-tooling/seer-upstream.md`'s "one project needing it is a
maybe; two confirms it" rule, this module (PSP-SDK-wide, zero game-specific
logic) is now a strong `@seer-project/pipeline` promotion candidate — not
yet migrated, tracked as `docs/the3rdbirthday/TODO.md`'s
`tfb-upstream-atrac3p`.

**Mop-up session (2026-09-13): one item closed, four advanced.**
`tfb-psmf-av-mux` is **closed** — `tools/shared/ffmpeg.ts`'s new
`muxVideoAudio()` (video stream copy + AAC-reencoded audio, `-shortest`)
now ships one playable MP4 per PSMF entry instead of a video-only MP4 plus
a separate WAV; 42/42 muxed with real audio, verified via `ffprobe` (both
streams present, matching ~32s durations) and raw PCM sample inspection
(thousands of distinct values, full dynamic range). The `3rd.fsd`
"unexplored ~1,792-byte region" is now a **confirmed real cross-reference
table** (not padding) — found by brute-force diffing every nonzero word in
it against the already-parsed file table's own `byteOffset` values (the
"two independently-located tables agreeing" oracle, applied mechanically):
28-byte records byte-exact-pointing at 10 specific real entries across 4
content types; *why* those 10, and 2 per-record fields, stay open. The 25
`other`-typed fsd entries are **partially classified**, not one format: fsd
14 is a complete, human-readable ~114-record stage/level name catalog
(`"ep01_st17 : EMILY_BOSS"`, plus internal `hexa_tst_*` test levels —
`hexa` = HexaDrive, this game's developer, independently corroborating a
fact previously only known from web search); fsd 12/27 are likely per-stage
sound/asset-ID lists; fsd 19 is a large self-describing directory+record
structure (semantics of its records unresolved); a small family
(fsd 320/321/323/324) has a texture-descriptor-shaped header whose pixel
payload didn't decode as plain RGBA at any guessed dimension. SEDBSSCF's
common header fields are now mapped past just magic+version, and the
15 RIFF-less entries (already known not to have a findable RIFF/WAVE
chunk) are confirmed to be **exactly the contiguous fsd-index run 33-47**
with **zero** audio-container magic anywhere in their full content (not a
truncated-scan artifact — every one is under 700KB, well inside the
already-used 2MB scan window) — their offset-table shape differs
structurally from the RIFF-having entries', pointing at a multi-clip
voice/dialogue-bank hypothesis, not decoded to individual audio.
`tfb-pack-count8`: the 91 `count=8` "effect bundle" packs (no main-resource
geometry) turn out to have real, decodable T4/T8 texture tables after all —
**6,195 textures**, verified by render, now shipped as standalone
`type: "texture"` manifest entries — corpus-wide texture decode is now a
clean 6,488/6,488 with 0 format-decode failures anywhere. This surfaced a
**second instance of the same discriminant-gating bug** documented in
`discriminant-gated-field-convention-applied-unconditionally.md`:
`parsePackTextureTable()` had never been gated by the already-existing
`hasConfirmedGeometryLayout(f0c)` check `parsePackGeometry()` already had,
so calling it on the 14 rare-header packs produced thousands of
garbage-`pixelFormat` descriptors (values up to 4,294,967,295) — caught by
a fresh regression test, not by inspecting shipped assets (the pipeline's
own downstream format filter had already silently protected the real
output). Fixed by adding the identical guard; see that lesson file's new
addendum. The `count=8` geometry/effect-chunk question itself, the 14
rare-header packs' geometry pointer, and `tfb-pack-bonematrix`'s bone
matrix search (still blocked on `eboot.bin` encryption) remain open — see
`docs/the3rdbirthday/TODO.md`.

## Corpora-index row text formerly inline in `game-re.md`

Moved verbatim from the always-loaded agent prompt during the 2026-10 restructure.

| `~/Development/parasite` | Parasite Eve (PSX, SLUS-00662) + Parasite Eve II (PSX, USA, a genuinely different codebase in the same repo — do not assume format compatibility between the two beyond what's independently verified) — 562 standard TIM bitmaps, 47 FMV movies, and 53/53 `AKAO` music/SFX collections (47/53 audible; the rest blocked on an upstream vgmtrans SMF-channel-ceiling limitation) all solved and shipped. The actor-package chunk container (shared header+slot-directory shape across all 3 chunks, `re-codebreaker`-cracked) underpins everything else: chunk3's 3D model + skeletal-topology format ships **830/830 models** as textured glTF (bone-local vertices, UV-space-unwrap texture bake, 0 `@gltf-transform/cli` errors) — the original 136/136 signature check was overfit to one reference field (`h[12]`, real per-model data, not a magic constant, see `model-signature-field-mistaken-for-magic-constant.md`) and relaxing it unlocked the rest. Per-bone rotation is confirmed genuinely absent from the model/bone-table format itself (direct per-bone vertex-extent measurement, not just unfound); a follow-up session found it lives instead in the animation-CLIP resource (chunk3 slot 3) and fully cracked that byte grammar via a `ghidra-disasm` trace of `SLUS_006.62` (directory + per-clip header + independently-constant-or-per-frame translation/rotation tracks, 8-bit and 16-bit rotation-sample variants, a hand-rolled fixed-point Euler->matrix builder, and PSX-GTE-opcode hierarchical FK composition) — verified two ways with no external oracle needed: byte-exact whole-corpus consumption (9,042/9,042 clips, 0 remainder) and a novel **FK distance-preservation** check (parent-child world-space distance must equal the bone's own already-confirmed static length iff the whole decode chain is correct; 0 exceptions/106,444 sampled bone-frame pairs, max error ~2.27e-13 — see `fk-distance-preservation-verifies-rotation-decode.md`, sourced from here). 721/830 models now ship the REAL decoded bind pose (superseding the old heuristic — `tools/shared/psx-actor-pose.ts` remains the fallback for models with no matching clip) and 715/830 ship real glTF skeletal `AnimationClip`s (rigid one-bone-per-vertex skin, `tools/shared/psx-actor-animation.ts` + extended `psx-actor-model-gltf.ts`); this pass also fixed two real glTF-validator bugs (a degenerate-triangle zero-normal fallback, and `SKIN_NO_COMMON_ROOT` on multi-root skeletons via a synthetic armature node). See `genuine-off-by-one-loop-matches-placeholder-record-convention.md` (sourced from here) for a confirmed-intentional decode-loop bound this surfaced. **Correction (2026-09-11):** a real track-index off-by-one survived all of the above — the clip's confirmed `+1` extra rotation track is a LEADING, not trailing, placeholder, so bone `i` needs track `i+1`; every bone was getting its next sibling's real rotation instead of its own. Both numeric oracles above are provably blind to this (neither cares WHICH valid track is read, only whether a length/byte-count invariant holds), and a prior session's own claimed Playwright visual check was false — a real re-check found every skinned model collapsed at the rest pose itself, root-caused by comparing mirror-pair limb directions in a plain wireframe plot (a synthetic-armature-node joint-index-shift hypothesis was checked and refuted first), fixed, and reverified both numerically (a new structurally-detected mirror-pair-direction regression test, 645 real pairs, median cosine 0.73→0.996) and visually (5 models re-screenshotted across every real clip). See `length-invariant-blind-to-track-index-misalignment.md`. **Correction (2026-09-11, later same-day session):** that "coherent standing figures" claim was only partially true — independent re-verification found the lower body renders correctly but everything above the waist explodes into disconnected fragments for 775/830 models (>1 bone with `parentIndex===-1`, up to 14), a SECOND bug the first pass's numeric oracles (FK distance-preservation, mirror-pair cosine) are provably blind to (see `statistical-proxy-blind-to-whole-body-visual-defect.md`, sourced from here). A principled partial fix (secondary roots compose onto the true root's world rotation) shipped but is mathematically proven insufficient (rigid rotation about a fixed point preserves distance, not direction) — escalated to `re-codebreaker`, which found `FUN_8003a088` never reads `parentPlus1` at all: it executes a bone-hierarchy stack program (a byte stream inside the model resource, located by tracing `FUN_8003d050`'s pointer chain), and `parentPlus1` is really a hierarchy ROW index into a REAL animated root node (row 0, the record `tryParseModel` had always skipped as "inert") every bone — not just a lucky first one — should compose against; verified 15,641/15,641 bone records across 830/830 models reproduced exactly by decoding that program, plus an independent from-scratch stack-machine replica matching the shipped composition to `<1e-9`, mutation-tested against both the original bug and the escalation's own briefly-shipped H_fix1 regression (caught as a live regression by byte-diffing the assets on disk, not just re-derived from theory). The escalation also surfaced a second, genuinely separate presentation-layer bug it correctly diagnosed but didn't itself fix — PSX is Y-down, glTF/three.js is Y-up, and nothing flipped it, which is what actually produced the "totem pole" screenshots both this session and the escalation's own images showed. A same-day follow-up fixed that too (a single Y-flip via proper rotation-matrix conjugation, `R'=F·R·F`, not naive component negation, confined entirely to the export layer so the fully-tested PSX-native core needed no change), independently re-verified via three convergent methods (a from-scratch triangle-mesh plot of the shipped static positions, a live extraction of three.js's own computed skinned vertex positions matching the static bake to float32 noise, and fresh Playwright screenshots of 6+ models at rest and mid-animation all showing coherent, right-side-up standing figures/creatures) before trusting either fix — see `verify-escalation-artifacts-not-just-claims.md`. **"Prerendered" room backgrounds were first closed as a confirmed negative, then fully overturned**: chunk3 slot 6's "scene blob" (trigger/zone array + per-tile placement/texture records) drives a real runtime tile-scatter compositor sampling chunk1's own VRAM pages — a mechanism a disc-I/O-scoped census is structurally blind to, since it composites from data already resident in the ordinary actor-package load (see `disc-io-census-blind-to-already-loaded-data-consumer.md`, sourced from here). Ships 509 room-background PNGs across 414 packages (`tools/shared/psx-tile-scene.ts` + `tools/parasiteeve/actor-background-scenes.ts`), after a follow-up session fixed two real bugs in the first-pass decoder: a two's-complement sign-convention error on the tile-placement bitfields (really unsigned — see `corpus-wide-zero-minimum-plus-contiguous-row-confirms-unsigned-field.md`, sourced from here) and a missing per-room grouping (several simultaneously-"active" triggers sharing a package are mutually-exclusive camera angles gated by a separate runtime-compared discriminator field, not simultaneous content to combine — see `active-flag-plus-runtime-discriminator-means-mutually-exclusive-not-combined.md`, sourced from here), both confirmed at the instruction level by a `ghidra-disasm` trace. Also fixed a real `always-full-run-manifest-merge-accumulates-stale-entries.md` instance the room-splitting fix triggered (a package's output filename *count* changed between runs). A later pixel-census-driven pass fixed two more real bugs in this same background compositor: an opaque-black unpainted-region fill that made 42/509 images >=95% solid black (see `opaque-fill-for-unpainted-region-is-a-false-visual-claim.md`, sourced from here) and, the actual root cause of all 6 *100%*-black images, a `tileCount` field that's an allocated-capacity value with a trailing run of fully-zero placeholder tile records (0 exceptions/306,620 tiles corpus-wide) that the old code painted as fake black tiles AND fed into the room's bounding-box computation (see `declared-record-count-is-allocated-capacity-trailing-zero-run-is-padding.md`, sourced from here). A residual handful of rooms (`actor346`/`359`/`381`/`430`/`428`) still render real (non-placeholder) tiles as black because their own on-disc CLUT upload is genuinely near-blank — confirmed by direct byte comparison against a healthy room's equivalent block, not a decode bug; tracked as `pe-tile-scene-blank-clut-rooms`. Remaining open items (bone-table unknown fields, a minority "group 0" animation-clip ownership scheme, the shared status-UI "bust card" bank's own pixel format, a few chunk3 slots) tracked in `docs/parasiteeve/TODO.md`. Surfaced format-porting pitfalls `quad-uv-array-winding-differs-from-index-array-winding.md`, `validation-sentinel-scoped-to-sub-region-not-whole-array.md`, and test-authoring pitfall `one-based-first-index-sum-is-total-minus-one.md` **Parasite Eve II** (first-pass exploratory session): container/chunk framing (`STAGE0.HED`+`STAGE{0..5}.CDF`, LZSS `.pe2pkg`/`.pe2img`/`.pe2clut`, `.spk`/`hSPK` audio, TMD models) identified and cross-verified byte-exact against a real, active community decompilation project (`GabeRealB/parasite-eve-2-decomp`) rather than derived cold; one real correction found to that project's own doc (a chunk-size field's unit — see `format-doc-prose-may-describe-converted-value-not-raw-field.md`, sourced from here). PE2's `INTER{0,1}.STR` cutscene-movie corpus confirmed byte-identical in container format to PE1's own FMV corpus and decoded end-to-end (39/39 heuristic per-cutscene segments, ~26 min combined runtime) by reusing PE1's `tools/shared/psx-str-xa.ts`/`ffmpeg.ts` unmodified — a positive worked example of verifying (not assuming) format compatibility before reuse. PE2 does not use the AKAO audio family at all (confirmed absent from vgmtrans's own per-title AKAO version history, and by real `hSPK` magic bytes) — a different in-house `.spk` sound-bank format instead. Also surfaced `file-named-dummy-may-hold-real-leftover-content.md` (sourced from here: PE2's `DUMMY.DMY` opens with a well-formed, non-standard-resolution MDEC bitstream header and is ~100% non-padding content almost to EOF). A later session **solved `.pe2pkg` room-package LZSS and TMD 3D model geometry**: the community project (checked fresh, not from the earlier session's stale "2 of 23 opcode families" read — see `tracker-prose-is-not-evidence.md`'s external-reference-project variant) had since fully mapped all 23 TMD draw families and shipped a complete LZSS decoder, both ported (`tools/shared/psx-pe2-lzss.ts`, `tools/parasiteeve2/pe2-tmd.ts`) and independently verified — LZSS byte-exact 448/448 against a real run of the community project's own `extract.py` directly against this project's actual disc files (0 mismatches, 0 unmatched extras; see the SHA-1-set-comparison technique note above), TMD geometry confirmed via exact reference-cited vertex/part/face counts (Kyle's body: 300 verts/20 parts/398 faces, exact) and real Playwright screenshots of 3 structurally distinct rendered models (a human female character, an armoured winged creature, a hunched clawed monster — all coherent, correctly proportioned, standing). Ships 598 static (rest-pose, untextured) glTF meshes. **A follow-up session solved TMD model textures end-to-end**: unlike generic 2D UI/map textures (which need an offline CLUT-row guess), each TMD primitive stores its own absolute `tpage`/`clut` fields directly in the geometry stream, so no guessing was needed — only decoding the room-package's own sibling Image (`0x1`, `.pe2img`)/CLUT (`0x2`, `.pe2clut`) chunks into a real PSX VRAM buffer (`tools/parasiteeve2/pe2-texture.ts`, ported from the community project's `image_codec.py`) and sampling it with PE1's existing `tools/shared/psx-actor-vram.ts` GPU-hardware helpers **completely unmodified** (they implement generic `getTPage`/`getClut` PSX conventions, zero PE1-specific logic — confirmed by porting them to a second game with no changes). 568/598 models shipped with a real baked texture (26 have no sibling image data at all and correctly ship untextured), verified via Playwright screenshots of 6 structurally diverse models (2 playable characters, 3 monsters, 1 soldier NPC — all coherent, correctly textured, non-garbled) and `@gltf-transform/cli validate` (0 errors/warnings across every sampled GLB). This session also produced a real, generalizable false-lead-and-correction: a disassembly-confirmed function (`Gp_PumpTmdStream`) unconditionally overrides a model's texture-page bias for objects reachable from a spawn site sharing the target's own load address, which looked like strong specific evidence for Kyle's body model — but applying it moved every resolved VRAM coordinate completely outside the file's own decoded texture data, while the *default* zero bias matched byte-for-byte. See `confirmed-generic-mechanism-may-not-apply-to-this-instance.md`, sourced from here. Separately, the per-bone animation-track format (`GpAnimSet`/`GpAnimRec`) is now structurally decoded and verified (`tools/parasiteeve2/pe2-anim.ts`: Kyle's block resolves to exactly 34 sets x 20 tracks, matching the community doc's documented count exactly, with the reference tool's own `walk_consistent` self-check holding 34/34) but deliberately **not** wired into glTF skinning/playback — the limb rotation keyframe's exact bit-packing has no strong verification oracle available (the obvious cheap check, FK parent-child distance preservation, is blind to rotation-only bones, since any orthonormal rotation trivially preserves distance regardless of correctness), and shipping unverified skinning risks exactly the class of silent bug documented elsewhere in this project (`bind-pose-render-blind-to-joints-index-space-bug.md`). A later session **solved PE2's `.spk`/`hSPK` audio sample pool AND the previously fully-undocumented `hONE` SndScript event grammar** (byte-exact SPU-ADPCM vs. the community project's own `spk_codec.py`; the event grammar derived first-hand from that same project's `src/main/sndscript.c`, which turned out to already be fully decompiled despite its own doc claiming otherwise — see `reference-project-doc-claims-stale-vs-own-current-source.md`, sourced from here) and **built this account's first PSX MDEC pixel decoder** (`tools/shared/psx-mdec-bs.ts`, verified pixel-exact against a reference decoder on `INIT.BS`'s legible boot logo), applied with zero changes to room-background chunks (1,759 unique, 100% clean decode, real recognizable art). Still open: the ~35 non-`TmdSource`-backed model streams, a small (~4-model) texture-residual gap, real skeletal playback (in progress), `.spk` timed/sequenced playback (samples + grammar decoded, not sequenced; a small oneC/Loop anomaly open), and room-to-background id mapping. See `docs/parasiteeve2/psx/data-structure.md` and `TODO.md` for the full survey. **The 3rd Birthday** (PSP, 2011, a spin-off with a wholly different engine): the `3rd.fsd`/`3rd.pkg` segment-addressed container (8-byte entries, sizes derived by sorting on segment start and diffing to the next entry, sentinel-terminated) cracked via a XeNTaX forum thread's prose (recovered through blocked-`WebFetch`-page `WebSearch` snippets, see `game-re-tooling/format-discovery.md`) with zero `eboot.bin` disassembly needed; PNG/PSMF-video/SEDBSSCF-audio all shipped (12/42/271 real assets); the PSP `sceMpeg` ATRAC3+ PES-walk mechanism first built in `~/Development/valkyrie` was ported verbatim and confirmed byte-exact on this second title, now a real `@seer-project/pipeline` upstream candidate. The largest category, `pack` (57% of the corpus), is now **SOLVED**: a `re-codebreaker` escalation cracked its main-resource payload as verbatim PSP GE (`sceGuDrawArray`) native vertex-array data, self-describing via a literal `pspgu.h` vertex-type bitmask plus redundant per-block stride/weight-count bytes (231/436 packs, 5,584 blocks, 318,336 vertices, 0 self-check deviations), with both indexed texture formats solved as a side effect (`pixelFormat` is this game's own bit-depth tag, not the literal `pspgu.h` `GU_PSM_*` enum a first pass assumed — `4`=T4/4bpp, 6,131/6,488; `8`=T8/8bpp, 357/6,488, initially misidentified as `GU_PSM_DXT1` by enum-number coincidence and corrected the same day via a payload-size oracle + render, see `pixel-format-value-guessed-from-enum-not-confirmed.md`). A generic, engine-agnostic `tools/shared/psp-ge-vertex.ts` (any PSP title uploading vertex buffers straight from a file can reuse it) plus a from-scratch `pack`-specific decoder + glTF exporter ship 231 real, `@gltf-transform/cli`-validated static glTF models — the independent re-implementation caught and fixed a real bug the escalation's own doc had already flagged in prose but a first coding pass missed anyway (the dominant shapes' geometry-pointer convention doesn't apply to the corpus's 14 rare header-variant packs; an ungated read produced 10 spurious garbage-geometry packs until a whole-corpus self-check test caught it — see `discriminant-gated-field-convention-applied-unconditionally.md`). Block-header `extraWords` is now also **SOLVED**: a stateful, per-pack bone-matrix-register delta list (`slotIndex,boneId` pairs applied cumulatively across a pack's whole block sequence) mirroring the real PSP GE `sceGuBoneMatrix` hardware convention of register-state persistence across draw calls — 0 contradictions across the whole corpus (5,584/5,584 blocks), resolving two prior sessions' "doesn't fit a clean pattern" verdict; see `hardware-register-persistence-explains-sparse-delta-metadata.md`. The actual bone **matrix/transform** data stays unfound after an exhaustive in-container search (pointer tables, brute-force block rescans, a whole-file count+float sweep, effect sub-chunks, the unclassified `other`-typed fsd entries) — `eboot.bin` disassembly, the only remaining avenue, is a confirmed dead end for now: it's a retail `~PSP`-tagged (KIRK/AMCTRL-encrypted) EBOOT and this project has no PSP decryption tooling on hand (see `game-re-tooling/psp.md`). Models ship static/unposed rather than with a fabricated skin. Still open: the bone-matrix palette itself, the 91 `count=8` effect/cutscene packs' actual geometry (their real, decodable T4/T8 **textures** now ship standalone regardless — 6,195 of them, corpus-wide texture decode is a clean 6,488/6,488 — a mop-up pass found this shipping path had reintroduced the identical discriminant-gating bug in a second function, `parsePackTextureTable()`, see that lesson file's addendum), and the 14 rare-header-shape packs. That same mop-up session (2026-09-13) also closed `tfb-psmf-av-mux` (PSMF video+audio now muxed into one file, 42/42), and found real, partial structure in three more previously-opaque areas: `3rd.fsd`'s "unexplored" header region is a confirmed real cross-reference table (found by diffing its words against the already-parsed file table's own offsets), a full human-readable stage/level-name catalog among the `other`-typed entries (independently naming the developer, HexaDrive), and a structural (not byte-level) multi-clip-voice-bank hypothesis for the 15 SEDBSSCF entries with no RIFF chunk (confirmed to be exactly fsd indices 33-47) | `game-re-corpora/parasiteeve.md` |

## Lessons sourced from this corpus (full list)
`validation-sentinel-scoped-to-sub-region-not-whole-array.md`, `quad-uv-array-winding-differs-from-index-array-winding.md`, `one-based-first-index-sum-is-total-minus-one.md`, `canonical-local-rest-frame-tests-rotation-necessity.md`, `golden-angle-sibling-fan-avoids-axis-collision.md`, `genuine-off-by-one-loop-matches-placeholder-record-convention.md`, `fk-distance-preservation-verifies-rotation-decode.md`, `verify-escalation-artifacts-not-just-claims.md`, `length-invariant-blind-to-track-index-misalignment.md`, `statistical-proxy-blind-to-whole-body-visual-defect.md`, `disc-io-census-blind-to-already-loaded-data-consumer.md`, `data-table-stores-prepacked-value-code-census-misses-it.md`, `domain-refuted-by-shape-not-values.md`, `corpus-wide-zero-minimum-plus-contiguous-row-confirms-unsigned-field.md`, `active-flag-plus-runtime-discriminator-means-mutually-exclusive-not-combined.md`, `always-full-run-manifest-merge-accumulates-stale-entries.md`, `opaque-fill-for-unpainted-region-is-a-false-visual-claim.md`, `declared-record-count-is-allocated-capacity-trailing-zero-run-is-padding.md`, `model-signature-field-mistaken-for-magic-constant.md`, `format-doc-prose-may-describe-converted-value-not-raw-field.md`, `tracker-prose-is-not-evidence.md`, `python-floor-division-port-to-js-silent-fraction.md`, `confirmed-generic-mechanism-may-not-apply-to-this-instance.md`, `reference-project-doc-claims-stale-vs-own-current-source.md`, `terminator-scan-must-be-record-aligned.md`, `file-named-dummy-may-hold-real-leftover-content.md`, `stock-sdk-routine-official-docs-outrank-disassembly.md`, `bind-pose-render-blind-to-joints-index-space-bug.md`, `small-sample-probe-undercounts-dominant-subformat.md`, `pixel-format-value-guessed-from-enum-not-confirmed.md`, `discriminant-gated-field-convention-applied-unconditionally.md`, `hardware-register-persistence-explains-sparse-delta-metadata.md`
