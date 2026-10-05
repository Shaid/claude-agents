# An external reference/decomp project's own prose docs can describe a stale, earlier state of that same project's current checked-out source

**When it bites:** a community/fan reference or decompilation project's own
written documentation (a format-notes file, an `ASSET_FORMATS.md`-style
doc, a README) states that some function or format is still unreversed,
unimplemented, or `INCLUDE_ASM`/binary-only — before accepting that claim
and either giving up on the sub-format or reaching for a different oracle,
grep the project's *actual current source* for the claimed marker/gap
directly.

This is distinct from `tracker-prose-is-not-evidence.md`, which is scoped
to the *target game project's own* internal tracking docs (its `TODO.md`/
`plan.md` describing itself) — here the doc in question belongs to a
separate, external reference/community tool, and the staleness is between
that tool's own docs and that tool's own source, with no bearing on
anything in the RE session's own project. It's also distinct from
`reference-tool-data-revision-mismatch.md` (which is about the *data* a
reference tool ships being a different game revision) — this is about the
tool's *prose documentation* lagging its own code.

Confirmed on Parasite Eve II (PSX, `parasite`): the community decompilation
project `GabeRealB/parasite-eve-2-decomp`'s own `doc/ASSET_FORMATS.md` §10.1
states that `SndScript_Exec` — the interpreter for the `hONE` SndScript
event-stream format used by `.spk` audio banks — is still `INCLUDE_ASM`
(i.e., not yet decompiled, function body opaque). Taking that at face value
would have meant treating `hONE`'s grammar as needing to be derived from
scratch by binary/structural analysis alone, with no source oracle
available. A direct `grep -n "INCLUDE_ASM" src/main/sndscript.c` on the
actual checked-out repo returned **zero hits** — the function is fully
decompiled, real, matched C, and reading it directly yielded the complete
`oneV`/`oneC`/`Wait`/`Loop`/`endL`/`endC`/`oneA`/`oneE` tag grammar
(including a genuine unconditional switch-case fallthrough between `oneC`
and `oneV` with no `break`, which no prose doc anywhere describes) in far
less time than a cold structural derivation would have taken.

The generalizable habit: an active community decompilation/RE project's
documentation is written prose, checked in alongside — not generated
from — its source, and can lag behind real progress the same way any
project's docs can (decomp projects in particular tend to update
`INCLUDE_ASM`/coverage-percentage claims in batches, not continuously).
Before trusting a reference project's doc that a target function/format is
still unreversed, `grep` its own source tree for the completion markers the
doc itself uses (`INCLUDE_ASM`, a stub/TODO comment, a raw byte-array
literal where decompiled code should be) — a few seconds of verification
that can turn a "no oracle exists, derive from scratch" problem into "the
answer is already sitting in a file you have local access to."
