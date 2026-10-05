# A multi-part formula correction can numerically cancel for the corpus's default/majority parameter value — verify the divergent branches explicitly, don't spot-check only the common case

**When it bites:** you've just ported a disassembly-confirmed correction
that bundles *several* related fixes into one formula (a new multiplier
term, a corrected divisor, a reordered roll) into a maintained
implementation, and you're about to sanity-check it against the existing
test fixtures — especially if those fixtures were all built against one
"typical"/default value of some input parameter (a command code, a mode
flag, a classifier byte) that the corpus rarely varies.

Two or more of the bundled corrections can arithmetically interact so that,
for the *default* value of the varying parameter, they exactly cancel —
producing a corrected-formula output that is either byte-identical to the
old, wrong formula's output, or a simple scalar multiple of it (2x, 0.5x) —
while the real divergence between old and new only shows up for
*non-default* parameter values the existing corpus happens not to exercise.

Confirmed on Valkyrie Profile (PSX, `valkyrie`): round 198 found the
physical damage formula needed 5 corrections, including a previously-
undocumented command-code-keyed multiplier (`{1,2,3}`, default `x2` for
every command code except two specific values) and a corrected classifier
divisor (an unconditional `/2` that a prior implementation omitted
entirely for the common "classifier == 0" case). For the DEFAULT command
code, the new `x2` multiplier and the new unconditional `/2` divisor
exactly cancel — so the classifier-0 branch's output became **exactly
double** the old implementation's, the quarter-classifier branch's output
came out **numerically identical** to the old implementation's, and the
divergence only appeared for non-default command codes, a "Weak Point"
elemental check, or a second, previously-missing graze roll. A test suite
built only from default-command-code fixtures would have looked like
either "nothing changed" (for the branches that happened to net identical)
or "everything doubled, that seems suspicious" (for the branch that
netted 2x) — both readings are wrong conclusions about a formula that was
correctly and faithfully ported.

**Fix:** after porting a multi-part correction, don't just diff old vs.
new output on the existing (likely default-parameter-heavy) fixtures and
declare victory or panic based on the aggregate delta. Trace *each*
individual finding to a fixture that specifically exercises its own
divergent case (a non-default parameter value, the branch the earlier
implementation didn't have code for at all) and verify that one
independently. Only after every individual mechanism has its own
targeted, divergence-exercising test should the aggregate "did the total
output change sensibly" check on the default case be trusted as
confirmation rather than treated as the whole story. This is the formula/
behavior-fix sibling of `sibling-field-values-alias-in-dominant-case.md`
(which covers two *storage fields* that alias for a dominant sub-case,
defeating a field-identity spot-check) — same root cause, a corpus/test
suite that under-exercises the discriminating case, but here it's a
*computed value's* branch coverage that's ambiguous, not which offset
holds a role.
