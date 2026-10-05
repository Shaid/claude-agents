# A mirrored per-frame dedup mechanism whose own broadphase gate tests a DIFFERENT bit than the one it produces is not a bug — the "wrong" bit is a real, separate signature from a third, unrelated mechanism, gating a deliberate mutual exclusion

**When it bites:** two (or more) structurally-parallel sibling mechanisms
each SET-and-self-test a dedicated bit in a shared per-frame status/dedup
word (mechanism A sets bit X and its own outer gate tests bit X; mechanism
B sets bit Y but its own, otherwise-identical outer gate tests a
*different* bit Z instead of Y) — and the asymmetry is provisionally
recorded as "unexplained," "not traced further," or "may gate something in
another function," without hunting for bit Z's own producer.

## What happened

Confirmed on Valkyrie Profile (PSX, `valkyrie`, `vp1psx-scene-script-opcodes`
campaign): two collision-primitive handlers (type 5 = a "drag volume", type
8 = a "confining slow zone") share one 16-bit per-frame dedup global,
mirroring their own occupancy flag into it every frame they fire (type 5 ->
bit 6, type 8 -> bit 7) so a later per-actor sync pass can refresh-clear the
flag if the primitive didn't fire again. Each handler's own outer
broadphase-skip gate reads that global first, to avoid re-running the whole
handler if it already resolved this frame. Type 5's gate tests its OWN bit
(bit 6) — the expected, symmetric shape. Type 8's gate instead tests bit 3
— a bit type 8 itself never sets. This was flagged at first sight and left
open for **ten sessions** across the row's own numbering (rounds 6 through
15) as "an asymmetry... not traced further this round."

The resolution: bit 3 has **no relation to type 8 at all**. It is a wholly
separate signature, produced exclusively by a THIRD, structurally unrelated
mechanism — a completely different collision-primitive type (a ladder-climb
engage) — set alongside its own producer bit as one combined `ori` mask.
Type 8's gate reading bit 3 is a deliberate, real **cross-mechanism mutual
exclusion**: the game does not want the confining-slow-zone response to run
in the same frame the actor engages a ladder (you cannot be doing both), so
type 8's dispatch is gated on "did a ladder get engaged this frame" as well
as on its own re-entry dedup. Bit 3 also turned out to have its own,
symmetric per-frame refresh (a persistent "on ladder" flag gets dropped if
bit 3 isn't set again the next frame) — i.e. it behaves exactly like every
other bit in the family, just for a mechanism nobody had connected to type 8
yet.

## The fix / general rule

1. **Don't file a mirrored-mechanism asymmetry as "unexplained" and move
   on.** If sibling producer A tests its own bit and sibling producer B
   tests a bit it doesn't itself set, that "foreign" bit is real evidence
   of a THIRD, as-yet-unidentified mechanism — go find that bit's own
   producer next, not more detail on A or B.
2. **A cross-referenced "foreign" bit in a shared dedup/status word is a
   free hint that two mechanisms are deliberately mutually exclusive**
   within the same frame/tick — checking the foreign bit's real producer
   usually explains *why* (a shared physical/logical resource, a shared
   input device, an incompatible state), which is worth writing up
   explicitly rather than just noting the bit identity.
3. **This is a distinct shape from
   `active-flag-plus-runtime-discriminator-means-mutually-exclusive-not-combined.md`**
   (which is about several SIMULTANEOUSLY-active records needing a second
   field to disambiguate which one applies) — this lesson is about ONE
   mechanism's own gate referencing a bit it never produces, which is the
   tell that a second, unrelated mechanism's state is being consulted for
   exclusion purposes, not about disambiguating multiple candidates of the
   same kind.
4. **Once the foreign bit's producer is found, re-verify it has no OTHER
   relation to the two mechanisms already in view** — in the confirmed
   case, the newly-found ladder mechanism also shared a *second* bit with
   one of the two original mechanisms' own downstream consumer (a shared
   "some solid foothold was resolved this frame" signature used by a
   completely different landing-state state machine), which would have
   been missed by treating the asymmetry as fully explained the moment one
   new producer was found. Finish a full bit-map census of the whole word
   before declaring the family closed.

Generalizes past this one game: any engine using one shared per-frame
"resolved this tick" word across several independently-triggerable
subsystems (physics contact types, animation-state machines, input-action
locks) can encode a real design constraint — "these two can't both be true
this frame" — as exactly this kind of asymmetric cross-reference, and it
will look like a copy-paste bug or dead code until the referenced bit's own
producer is traced.
