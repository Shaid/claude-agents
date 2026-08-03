# Hand-derived expected values in a new decoder's tests can encode your own bugs — generate fixtures by running the implementation or an independent oracle instead

**When it bites:** you've just written or landed a verified decoder/simulator
and are now writing its regression tests, and you're computing the expected
`toEqual(...)` values by reasoning about the algorithm on paper rather than by
executing something.

A freshly-verified decoder is not proof that your test *fixtures* are
correct — those are a second, independent hand-derivation, with its own
chance to be wrong, and a wrong fixture either fails a correct implementation
(wasting time chasing a phantom bug) or — worse — quietly encodes the same
mental-model error the implementation might have, so the test can never catch
that class of bug.

Two concrete failure modes hit while writing tests for WIME's
`SynthSceneObjects` reimplementation (`middilgard` project, a verified,
re-codebreaker-escalated simulator — see
`verify-escalation-artifacts-not-just-claims.md`):

1. **Assuming "unwritten" meant `undefined`.** The implementation's documented
   convention was "a field the case body doesn't write keeps whatever was in
   that array slot before." For a brand-new slot with no prior occupant, the
   real code defaults it to `0` — but several hand-written test expectations
   assumed `flags: undefined` instead, because "unwritten" was read as
   "absent" rather than "whatever the design's default-fill value is." Every
   one of these was wrong until the real implementation was actually run and
   its output pasted in as the fixture.
2. **Forgetting an earlier consumed value shifts every later one.** The
   function draws from a shared PRNG stream; an *entry-point* draw (consumed
   unconditionally before any case-specific logic) shifts which stream
   position every subsequent draw inside a specific case body reads from. An
   isolated hand-calculation that computed "what does selector N return for
   seed S" without first replaying the entry draw got a plausible-looking but
   wrong number — the kind of error that looks like a typo, not a logic bug,
   and is easy to miss on a self-review.

**Fix:** for any test asserting the output of code you just wrote (not a
long-standing, independently-trusted decoder), generate the expected values
by *running* the real implementation (or a fully independent oracle) with the
test's exact inputs and pasting its actual output into the fixture — never
compute "what it should produce" by hand and trust that derivation blind.
Reserve hand-derived fixtures for cases you can verify some other
way (an external oracle, a known-good reference render). This is cheap: one
throwaway script run, before the test is committed — not a process addition,
just a discipline about where the expected-value literal comes from.
