# A byte-exact differential oracle against the game's own routine is blind along every axis the harness feeds identically to both sides

**When it bites:** you verified a port by executing the *real* routine (under
a CPU interpreter/emulator harness) and diffing it against your
reimplementation, it matched byte-exact across every sampled input, a
negative control proved the comparison discriminates — and you are about to
treat the whole model as confirmed. Any state the routine *inherits* rather
than reads from the image (hardware/coprocessor registers set by an earlier
call, a base pointer, ambient configuration, a resident matrix or palette)
was supplied by your harness to both sides at once, so the diff can never
disagree about it.

## What went wrong

Valkyrie Profile (PSX): VP1's world-to-screen projector `fcn.80060044` (100
MIPS instructions, one GTE `RTPS`) was hand-ported to TypeScript and verified
by running the real routine off the disc image under the project's own MIPS
interpreter and diffing outputs. Result: **896/896 projections byte-exact**
across 4 camera configurations, with a negative control confirming the
comparison discriminates (perturbing the deadzone snap, the bob term, the
world-X centring constant, or the height scaling was each caught on 63-224 of
224 samples). That was a real, gold-standard result — and it was still
compatible with a completely wrong scene.

The routine contains **zero `ctc2`**: its `RTPS` runs against a GTE rotation
matrix installed by *some other* code, outside the traced function. The
harness installed an assumed matrix, identically, on both sides. So the oracle
passed with exactly the same 896/896 under an identity matrix as under the
correct one. Nothing about the verification could ever have flagged it.

The defect surfaced only on a completely different kind of check: wiring the
port into the real scene and rendering it in a browser, where **every unit was
off-screen**.

## The fix

Chasing it produced a real result rather than a patch. Sweeping camera
distance 100..8000 under an identity matrix put the game's own
already-confirmed formation anchors on the 320x240 display at **0 of 791**
sampled distances — screen X needs distance >= ~1000 while screen Y needs
<= ~400, and those windows are disjoint. Identity was therefore *refuted*,
not merely unconfirmed, and the resident matrix must carry a scale factor.

**The general discipline:** when a differential/execution oracle passes,
explicitly enumerate two sets before calling the model confirmed —

- what the traced code **reads from the image** (its own operands, literals,
  and struct fields): the oracle covers this, and covers it very well;
- what the **harness injects** (inherited coprocessor/hardware registers,
  base addresses, load bases, ambient configuration, anything set up by a
  caller you did not trace): this is the oracle's structural blind spot,
  and its size is exactly how much of the model is still unverified.

The injected set needs a *differently shaped* oracle — most cheaply an
end-to-end run or a render, which fails loudly and immediately when an
inherited parameter is wrong. A scan of plausible values for the injected
parameter, scored against independently confirmed data (here: real formation
anchors versus real screen bounds), can also turn "unconfirmed" into a
genuine refutation, which is worth much more than a fitted constant.

Sibling lessons, same family, different mechanism:
`oracle-check-blind-to-decoder-generated-extra-entries.md` (the oracle only
visits the indices it itself enumerates — a length/extent blind spot),
`length-invariant-blind-to-track-index-misalignment.md` (a conservation
invariant doesn't care *which* valid element was read), and
`statistical-proxy-blind-to-whole-body-visual-defect.md` (a proxy metric
measuring relative agreement, not absolute correctness). The distinguishing
feature here is that the oracle *is the original binary executing real
instructions* — the strongest oracle available — and it still has an axis it
cannot see.
