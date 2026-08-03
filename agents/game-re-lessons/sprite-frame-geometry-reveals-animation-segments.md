# Sprite frame bounding-box geometry can recover animation-segment boundaries when the driving executable can't be traced

**When it bites:** need a frame-index → named-animation mapping (idle,
walk, attack, death, ...) within a multi-frame sprite/animation resource,
and the executable that would authoritatively drive playback has no symbol
table, is an overlay/packed structure, or otherwise resists tracing (so a
byte-pattern search for the resource's own id inside it turns up only
chance-level hits in code/strings, not a frame-range table).

Two cheap, code-computable structural signals recovered a real segment
boundary directly from each frame's own bounding box (width/height), with
zero executable tracing, on Warriors of Legend's LMRF sprite corpus
(middilgard project):

1. **A sustained bounding-box discontinuity.** A segment boundary is a
   frame where width (or height) jumps by more than some ratio (e.g. 1.6x)
   relative to the preceding segment's median, **and** the new value stays
   in that regime for several consecutive frames afterward (a "plateau"
   requirement, e.g. >= 4 frames) rather than being a one-frame blip.
   The plateau requirement is what separates a real segment change from
   ordinary single-action motion: a sword swinging through a full arc
   within *one* animation changes frame-to-frame width just as much as a
   real segment cut does, but never settles into a new sustained range —
   confirmed on a 5-frame attack-swing resource whose width changed nearly
   every frame yet triggered zero false-positive boundaries, versus a
   16-frame resource with a clean, 8-frame-sustained ~2x jump that matched
   a real idle-to-attack transition confirmed by rendering.

2. **Cross-resource exact frame-dimension prefixes — a structural, non-
   visual proof.** When resource A's *entire* frame-dimension sequence
   (width and height, in order, for every frame) matches resource B's
   *first* N frames exactly, and B has more frames than A, that is proof a
   real, authored boundary exists at frame N in B — not a guess from a
   geometric heuristic, since two independently-addressed resources agree
   on it. This catches real boundaries the width-discontinuity check
   misses entirely: several confirmed pairs had a genuine idle→attack cut
   whose attack motion stayed *inside* the idle segment's width envelope
   (a small dagger stab, not a big axe swing), invisible to signal #1 but
   caught immediately by the exact-prefix match. A full pairwise
   dimension-sequence comparison across a same-file resource corpus is
   cheap (a handful of resources out of 162 in this case) and worth running
   before concluding a corpus has no such relationship.

**Naming is still a best-fit label, not free.** These signals prove *where*
a cut is, not *what* each segment means — the segment's name still needs at
least one representative render check per distinct pose family, generalized
by analogy to render-unconfirmed siblings with the same structural shape
(and graded accordingly: confirmed / structural-but-unnamed / hypothesis —
see `published-walkthrough-numeric-oracle.md` and
`partial-resolution-rate-is-noise.md` for the same "some evidence proves a
fact exists, separately grade how much of the *semantic* claim it actually
supports" pattern in other contexts).
