# Multiple distinct small-data trampoline slots can cascade via short `BSR`s to one shared far `JMP.L`

**When it bites:** resolving a SAS/C (or similar small-data-model)
`JSR N(A4)` trampoline via the standard "read a 6-byte `4EF9<4-byte-addr>`
`JMP.L` stub at the computed hunk1/DATA offset" formula, and the bytes at
that offset don't start with `4EF9` — especially when the formula has
already been verified correct (against other, working trampolines) so a
mis-derived offset seems unlikely.

Not every trampoline slot in such a table is a standalone 6-byte `JMP.L`.
A linker can coalesce many logically-distinct small-data call sites that
all ultimately resolve to the *same* target function into a run of cheaper
4-byte `BSR.W` stubs, each with a displacement calibrated to land exactly
on one shared `JMP.L` stub placed at the end of the run — saving 2 bytes
per redundant slot versus duplicating the far jump everywhere. The result
looks, at a glance, like garbage (`61 00 00XX` instead of `4E F9 ....`), but
is fully valid, deliberate code: hand-tracing the `BSR.W`'s own PC-relative
math (`target = (address_of_displacement_word + 2) + displacement`) shows
every slot in the run reaching the identical final address.

Confirmed on Wings (Amiga): two structurally distinct-looking small-data
calls (`-31270(A4)`, used 150+ times for what call-site shape suggested was
a "project world point to screen" primitive, and `-31222(A4)`, used far
less for what looked like a distinct "edge/line setup" helper) both
resolved, byte-exact, to the same hunk0 target (`CODE+0x908E`) — not
because the resolution formula was wrong, but because the hunk1 table held
an 8-byte-stride run of descending-displacement `BSR.W` stubs (`0xb6` down
to `0x06`, step `-8`) all converging on one `4EF9`-prefixed `JMP.L` at the
run's end. Naively assuming "different `N(A4)` value must mean different
target" here would have produced two false-distinct routine identities for
what is actually one shared function (its exact role — full 3D projection
vs. a narrower 2D helper — was left as a separate, still-open question,
but the two call sites are now known to invoke the identical code).

**Fix:** if bytes at a computed trampoline offset don't start with the
expected far-jump opcode, don't assume the address math is broken before
checking for a short relative-branch opcode instead (on 68k, `0x6100` =
`BSR.W`, followed immediately by a 16-bit signed displacement word) and
hand-computing its target. If several nearby slots (fixed stride, e.g. 8
bytes apart here) show the same opcode with a *linearly decreasing*
displacement, that's the signature of exactly this coalescing pattern —
trace one or two to their shared endpoint to confirm, rather than treating
each slot as an independent unresolved case.
