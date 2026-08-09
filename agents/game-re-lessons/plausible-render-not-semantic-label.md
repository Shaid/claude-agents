# A recognisable render confirms the pixel decode, not the semantic label you guessed for it

**When it bites:** a specific entry in an already-decoded frame/state/
animation table (e.g. "frame 0") rendered as a recognisable, plausible
instance of a *guessed* semantic label ("standing pose", "idle", "default")
during an earlier decode pass, and that label has been carried forward in
docs/code/tests ever since — especially when the *actual* frame-selection
code (which byte/table value the game uses for that specific labelled
state, at runtime) was never traced, only the pixel decode was.

Confirmed on FFVI (SNES, `ceres` project): an early session decoded
`MapSpriteTileOffsets` entry 0 for the field/overworld character-sprite
format and rendered it — correctly, pixel-exact — as a recognisable
standing character, and documented it as "frame 0, the confirmed standing/
facing-down pose." That pixel decode was never wrong. The *label* was: a
later session traced the field engine's actual frame-selection code
(`obj.asm`'s `ObjStopTileTbl`/`ObjMoveTileTbl`) and found entry 0 is never
selected by any facing's dedicated standing-pose table entry at all — it's
Down-facing's walk-cycle step 3 (the last step of `[1,2,1,0]`), reached
only mid-stride. It merely *looked* like standing because that particular
walk-cycle step happens to keep arms/legs close to a neutral rest position
— an accident of the source art, not evidence the guessed label was right.
The render passed the mission's visual-confirmation bar (immediately
recognisable, correct colours, no scrambling) at every point in this
story; only the semantic *label* attached to what was confirmed was wrong,
and it survived uncaught until the selection code was actually traced.

**The general check:** a render proves the bytes decode to the pixels you
see — full stop. It does not, by itself, prove *when* or *under what game
state* the engine actually uses that table entry, unless the selection
code was traced (or an equally direct oracle, e.g. a savestate/memory
capture during that exact game state, was used). Before writing a
confident semantic label ("standing", "idle", "walk-north") for a
render-confirmed table entry, ask: did anything actually establish that
*this specific value* is what the game selects for *that specific named
state*, or did the render just look plausible enough for the guessed label
to feel unremarkable? If the selection logic is findable (a disassembly,
a reference reimplementation, a bytecode VM — see
`sprite-frame-geometry-reveals-animation-segments.md` for what to do when
it genuinely isn't), trace it before finalizing the label, even when the
render already "looks right." When the correction does surface, it
doesn't invalidate the original decode/render (`renderFieldSprite`'s
frame-0 output is byte-identical before and after this correction) — it's
purely a documentation/labelling fix, and should be written up as a
`> **Correction:**` block in place, not a silent edit, exactly as this
project's own conventions require for any other overturned claim.
