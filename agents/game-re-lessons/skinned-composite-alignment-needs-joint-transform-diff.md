# Compositing two separately-exported skinned pieces at a shared scene origin needs a joint-transform diff first, not an assumption or a live-render trial

> **Correction: a clean diff on ONE pair is necessary but not sufficient —
> it must be repeated across every combination of the corpus's orthogonal
> axes, not trusted as a one-shot universal confirmation.** The original
> finding below (Byleth's own body+head, 88.6% shared-joint agreement, zero
> transform needed) was written up as a general rule and was wrong as one:
> it happened to hold only because Byleth's own personal body IS the
> corpus's shared "standard" male rig, so it trivially also agrees with
> every male CLASS body's joints too. A later corpus survey (8 personal
> bodies + 7 class bodies, both genders) found every FEMALE class body
> shares one uniform "standard" neck-bone world position, while every
> FEMALE personal body has its own distinct one — up to ~2 units apart on a
> ~166-unit skeleton, none matching the class standard. The
> personal-on-personal/male combination the original diff tested was the
> single most "already agrees by construction" point in the whole corpus;
> the female-on-class-body combination (a different value on EACH of two
> orthogonal axes — gender, and personal-vs-shared-class-body) silently
> disagreed, and no amount of re-checking the SAME pair would have
> revealed it. The practical symptom: female characters' heads sat visibly
> mis-seated (floating or sunken relative to the collar) on class bodies.
>
> **Fix, generalized:** before writing up a byte-level joint-transform diff
> on one pair as a corpus-wide "no correction needed" verdict, identify
> every orthogonal axis the real corpus varies along and require at least
> one tested example from each COMBINATION those axes can produce — not
> one example per axis independently, since two axes can interact (each
> axis alone was fine here; only their combination broke). A pair that
> sits on the corpus's most "standard"/default/reference combination of
> values is the LEAST informative point to generalize from, precisely
> because default content is the most likely to agree with itself by
> construction. When the survey does find a real per-combination
> disagreement, don't guess a per-axis fudge constant from the survey
> data — measure the correction per-pair at RUNTIME instead, from the two
> real loaded objects' own shared reference point (read both objects'
> identically-named joint node, take its world position via the scene
> graph's own transform composition, translate by the delta). This
> reproduces `(0,0,0)` — a true no-op — for every combination the original
> single-pair finding already covered, so it subsumes rather than
> contradicts that finding instead of needing to special-case it away.
> Confirmed fixing this exact case in the same `chimera`/Three Houses
> corpus the original finding came from.

**When it bites:** wiring up a viewer/exporter to composite two (or more)
skinned mesh pieces that were exported as **separate** GLB/glTF files from
a shared source rig — e.g. a body model and a head model that the source
game itself renders as two skinned pieces sharing one skeleton, but which
a per-resource exporter emits as two independent files, each with its own
`skin.joints[]`/`inverseBindMatrices`. The natural next step is either to
guess an alignment transform (an attach-socket offset, a bone-parented
translation) or to just add both at the origin and eyeball a render — both
are avoidable guesswork.

## The check

Parse both GLBs' JSON chunks directly (trivial — no external deps needed:
read the `u32` magic + `u32 jsonChunkLength` header, slice, `JSON.parse`)
and compare their `nodes[]` by name:

1. **Joint-name overlap.** If one piece's skin joints are a subset (or
   near-subset) of the other's, the two were very likely built from the
   same underlying bone naming/rest-pose data, not independently authored.
2. **Local-transform agreement on the shared names.** For every joint name
   present in both, diff `translation`/`rotation` (not `scale` usually,
   unless the source format uses non-uniform per-bone scale). A high
   agreement rate (not necessarily 100%) on the shared **root chain**
   specifically is the decisive signal: if the path from each piece's own
   scene root down through its first few ancestor joints matches
   byte-for-byte (down to float noise) between the two files, both pieces'
   skeleton roots already represent the *same* world pose when placed at
   the same origin — no alignment transform is needed, and adding both
   `Object3D`s (or equivalent) as siblings under one shared parent with
   identity transforms is the *correct* composite, not a placeholder.
3. **A divergent minority is not disqualifying.** A subset of shared-name
   joints disagreeing in transform AND parent (typically hair/cloth/jiggle
   "physics" bones near the tail of the name range) does not undermine (2)
   — it usually means the source format's bone-index/name space is reused
   per-asset for a *different* per-piece dynamics chain past the shared
   humanoid rig (see `locally-indexed-substructures.md`), which is
   harmless for compositing specifically: each piece's `SkinnedMesh` only
   ever reads its *own* file's joint array, so the two pieces' divergent
   bones never cross-contaminate each other. Only the *shared* subset's
   agreement matters for placement.

Confirmed on Fire Emblem: Three Houses (`chimera`, Switch): a character's
body GLB (183 skin joints) and head GLB (140 skin joints, a strict subset)
agreed on **124/140 (88.6%)** shared-name joints' local translation+
rotation, including the entire root chain (`bone0`→`bone1`→`bone2`,
byte-identical in both files down to float noise); the remaining 16
(hair/accessory jiggle bones, `bone124`-`bone139`) were parented to
*different* bones in each file (a different, per-pack physics chain reusing
the same small index range). Adding both pieces' `Model3D.object`s to the
same scene at the shared origin with **zero** extra alignment transform —
exactly what the diff predicted — produced a correctly-seated head on
every character/variant tried, verified visually via real screenshots
(no seam, no gap, no double-head artifact), not just by DOM-state checks.

## The generalization

This is the multi-piece analogue of `bind-pose-render-blind-to-joints-index-
space-bug.md`'s core lesson (a bind-pose render alone can hide a real
skinning bug) turned into a positive technique: a **byte-level structural
check on the two files' own skeleton data** — cheap, deterministic, no
emulator or live capture needed — settles the alignment question before
any compositing code is written, and is strictly more trustworthy than
"render it and see if it looks right," which can't distinguish "correctly
aligned" from "coincidentally close enough to not obviously notice" at a
typical viewer zoom level.
