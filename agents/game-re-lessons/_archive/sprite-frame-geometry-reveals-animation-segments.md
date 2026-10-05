# Sprite frame bounding-box geometry can recover animation-segment boundaries even when the driving executable resists tracing — or can't name states even when it's fully traced

**When it bites:** need a frame-index → named-animation mapping (idle,
walk, attack, death, ...) within a multi-frame sprite/animation resource.
Most often this is because the executable that would authoritatively drive
playback has no symbol table, is an overlay/packed structure, or otherwise
resists tracing (so a byte-pattern search for the resource's own id inside
it turns up only chance-level hits in code/strings, not a frame-range
table) — but **the same fallback is needed even with a fully-symbol-named,
completely traceable executable**, if the VM/interpreter driving playback
turns out to select behavior by an opaque numeric "state" or "entry point"
index with no caller anywhere that assigns it a semantic name (confirmed on
Vengeance of Excalibur, whose FSME entity-animation bytecode VM was fully
decoded down to the exact instruction encoding — `docs/vengeance/amiga/
engine.md` § "Entity Animation Bytecode VM" — yet still left "which of a
class's ~32 dispatch entry points is idle vs. attack vs. death" open,
because no code anywhere assigns state-index N a name). A traceable
interpreter tells you *how* frames are selected; it doesn't guarantee it
tells you *which* selection means what.

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

3. **A third, VM-derived signal when the interpreter is fully traced: a
   reachability walk over the bytecode's own frame-select instruction.** If
   the interpreter's opcode encoding is fully decoded (see
   `vm-bytecode-embeds-platform-addresses.md`'s "closed the loop" addendum),
   walking each of a class/object's dispatch entry points and collecting
   every literal frame index its bytecode can draw gives a real, code-derived
   grouping — confirmed on Vengeance's `knight` class, where entry points
   settle into a handful of distinct, mostly-contiguous frame sets. This is
   *stronger* evidence a boundary is real than either geometric signal above
   (it's not a heuristic — the frame numbers are literally read out of the
   game's own script), but it still only proves *grouping*, not *naming*:
   which group is "attack" versus "idle" still needs the same external
   check (render or corroborating geometry) as signals #1/#2, and it can
   disagree with them on the exact cut point without either being wrong —
   report both rather than forcing a false reconciliation.

4. **A geometric special-case criterion that fires for exactly one instance
   is not proof the *criterion itself* is what identifies the phenomenon in
   sibling instances — look for a co-located code-level marker instead.**
   WIME's FRML animation VM (same project) has a per-race swing region that
   splits into two frame families for several races; for the *wizard* race
   specifically, the second family's frames are both wider AND taller than
   baseline — a plausible "raised-arms/staff" visual tell for a spell-cast,
   confirmed by ground truth. Trusting that geometric criterion as *the*
   test for "is this a magic attack" would have missed two more races later
   confirmed (via ground truth) to also have a coded magic attack: wraiths
   and a Balrog, whose second frame family is a plain width-only shift with
   no height growth at all — indistinguishable by the wizard's own geometric
   rule from four *other* races' second family, which is genuinely just an
   alternate-footwork swing variant, not magic. The signal that actually
   generalized was a reserved bytecode opcode (`extra=0x80, code=16` in this
   VM's encoding) embedded directly inside the "magic" frame block — a real
   targeting/effect-resolution routine, confirmed present in exactly the
   wizard/wraith/Balrog blocks and absent from the other four races' blocks
   of the identical *structural* shape. The lesson generalizes: a visual
   artifact (extra height, extra width, a color change) is often a
   *side-effect* of what a marked block's code actually does for one
   particular instance (a human wizard visibly raises a staff; a wraith's
   equivalent effect has no comparable sprite content to grow into) — when a
   geometry check confirms a special case for instance A, search the
   surrounding bytes/bytecode for a marker before assuming instance A's
   *visual* tell is the generalizable test for instances B, C, ...

5. **Naming *can* be recovered with real confidence from the VM itself —
   the "no caller names entry point N" dead end (this file's intro
   paragraph) isn't universal.** A later session on Spirit of Excalibur
   (same engine family, sibling `middilgard` project) manually traced
   individual entity-class bytecode scripts end-to-end (not just a generic
   reachability walk collecting frame sets per entry point per signal #3,
   but reading the actual instruction sequence in program order) and found
   real naming evidence the generic walk can't surface: a backward `Goto`
   forming a genuine repeating loop with interleaved "move toward
   destination" instructions is a walk cycle with real confidence, not a
   guess; a forward-only ramp of increasing frame indices ending in a
   "freeze the current frame forever" sentinel, accompanied by a sound-effect
   opcode and a conditional spawn (loot/corpse), is a death animation with
   real confidence; a 2-frame alternating loop reached from a shared "check
   status" subroutine called from many unrelated points in the script is a
   guard/idle stance. The generalizable point: when the interpreter is fully
   decoded, don't stop at a structural reachability walk (signal #3) if
   frame-selection opcodes carry contextual siblings (timing/duration
   fields, sound/spawn/effect opcodes, sentinel values like "hold this frame
   forever") — those siblings are often enough to name a segment outright,
   not just delimit it. This is genuinely more expensive per class (each
   script traced by hand) than the generic walk, so budget it only for the
   classes/sprites that matter most, and expect it to work for some classes
   (the ones with a scripted death/idle) and not others (many NPC classes in
   the same corpus had no death sequence in their own script at all — it's
   handled by separate native engine code instead, a real finding in
   itself, not a gap in the trace).

6. **When two platform ports (or two builds) of the same sprite resource
   differ in frame *count*, a positional (index-by-index) dimension diff
   misattributes new content if the extra frames are inserted mid-sequence
   rather than appended at the tail — align by longest-common-subsequence
   (LCS) over each frame's own descriptive tuple instead.** A frame inserted
   at position K shifts every later frame's index by however many insertions
   preceded it, so positional diffing flags all of them as "different" even
   though they're pixel/dimension-identical, just relocated. Confirmed on
   WIME's DOS-VGA-vs-Amiga `BSCENE.RES` "man" FRML (`middilgard` project): a
   prior pass, diffing frame N against frame N across the two builds, wrongly
   concluded 3 tail frames (indices 17-19) were unique new art depicting a
   sit-down pose. Re-aligning the two frame sequences with a from-scratch
   LCS over each frame's `(width, height, composeX, composeY)` tuple (not
   raw pixels — dimensions were enough, and dimensions are what's cheaply
   available from an already-decoded frame table) proved those 3 "new" tail
   frames were byte-for-byte the *same* pre-existing content as the other
   build's frames 12-16, just shifted up by 3 because 3 *genuinely* new
   frames had been inserted much earlier, in the attack-swing region (an
   alternate weapon-swing variant, confirmed by tracing which frame indices
   the game's own animation bytecode actually references — a completely
   different semantic role than the "new sit-down pose" the positional diff
   had attributed to the wrong frames). The LCS realignment is cheap (frame
   tables are small, tens of entries) and should be the default comparison
   method any time frame *counts* differ between two otherwise-matching
   sprite resources — a positional diff is only safe when counts are equal.

**Naming is still a best-fit label, not free.** These signals prove *where*
a cut is, not *what* each segment means — the segment's name still needs at
least one representative render check per distinct pose family, generalized
by analogy to render-unconfirmed siblings with the same structural shape
(and graded accordingly: confirmed / structural-but-unnamed / hypothesis —
see `published-walkthrough-numeric-oracle.md` and
`partial-resolution-rate-is-noise.md` for the same "some evidence proves a
fact exists, separately grade how much of the *semantic* claim it actually
supports" pattern in other contexts).
