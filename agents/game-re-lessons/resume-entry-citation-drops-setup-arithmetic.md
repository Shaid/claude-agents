# A routine reached from two entry points: citing the resume/re-entry label silently drops setup arithmetic that only runs on the normal path

**When it bites:** disassembly shows a label with no incoming arithmetic
before it (e.g. a value gets loaded "directly" into a register with no
transform) being cited as proof a field is stored in some final/resolved
form — and that same label is also the target of a conditional branch from
a few instructions earlier in the same routine (a "was this operation cut
short last call, resume it" pattern), meaning it has two different possible
predecessors with different state guarantees.

## What went wrong

Wings (Amiga)'s Mode-B decompressor resolves an LZ back-reference "distance"
field against a persisted ring-buffer write cursor. An early pass cited
`LAB_6980` (`MOVE.W -12412(A4),D5` — load the distance global straight into
the read-index register, no arithmetic) as proof distances are stored as
**absolute** window positions: the encoder and decoder must track the same
state, so no subtraction against the cursor is needed at decode time. That
reading was internally consistent and matched the label's own instruction
exactly — but `LAB_6980` is the **resume** entry point, reached only via a
conditional branch (`TST.W <copy-in-progress-flag> / BNE.W LAB_6980`) taken
when a copy was cut short by a previous call's output-byte budget. The
**normal** entry point, which every one of the nine control-byte handlers
actually branches to, is two instructions earlier
(`LAB_6974`) and does:

```
MOVE.W  <cursor>,D0
SUB.L   <distance-global>,D0     ; D0 = cursor - distance
MOVE.W  D0,<distance-global>     ; OVERWRITE the global with the resolved position
LAB_6980:
MOVE.W  <distance-global>,D5     ; (resume path lands here)
```

The global is a **relative distance on the way in and an absolute position
on the way out** — which is exactly why the resume path can (correctly)
load it directly: by the time a paused copy resumes, the subtraction has
already run once and the global has already been overwritten in place. The
label cited as "proof" was real, its instruction was transcribed correctly,
and its behavior was correctly described — the citation was just anchored
to the wrong one of two valid entry points into the same code, and the
setup step that makes the *other* entry point's simpler-looking behavior
correct sat two instructions upstream, outside the cited window.

## Fix

Before citing a label as "this is what the CPU does with field X," check
whether anything branches **into** that label from elsewhere in the same
routine (not just whether it falls through from above). If so, identify
every entry point and read backward from the normal/primary one, not just
whichever label happened to be the first one your search or a jump-table
scan landed on — a resume/retry/short-circuit entry point is deliberately
missing the setup its sibling entry already performed, and reading it in
isolation will describe correct end-state behavior for a value while
getting its *stored representation* backward. This is a sibling of
`nearest-preceding-immediate-is-not-dataflow.md` (both are "the value
you're looking at was written somewhere else, not where you're reading it")
and of `confirmed-subroutine-does-not-bound-its-caller.md` (both are "a
correctly-read fragment of a routine doesn't mean you've read the routine")
— this variant's specific tell is a label reached by *both* fall-through
*and* an incoming branch from a flag-gated conditional a few instructions
earlier in the same function.
