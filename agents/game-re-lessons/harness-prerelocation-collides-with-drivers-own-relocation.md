# A boot harness's own pre-relocated addresses can be silently re-relocated a second time by the real driver code it then executes

**When it bites:** a harness bypasses a real hardware/driver load-time
handshake (a cross-chip transfer protocol, a DMA upload, a resource
loader) by directly placing already-correct, pre-computed addresses into
emulated memory, and then lets the *real* driver/game code run from that
point forward — especially when the bypassed handshake's job (per any
existing docs) is known to have included an address-relocation step of its
own.

Real driver/loader code very often re-derives its own working addresses
from data it just received, rather than trusting them as already-correct —
typically: read a "base" value from the transferred data (a header field,
a build-time-relative offset table), compute `delta = fixedRuntimeConstant
- base`, and add that delta to every raw stored pointer it subsequently
reads. If a harness has *already* pre-relocated those same pointers to
their final, correct addresses (for its own reasons — e.g. a custom,
budget-driven memory layout that doesn't match the real transfer
mechanism's own placement), letting this real relocation code run
unmodified composes additively on top of the harness's own correction and
produces silently wrong addresses — no crash, no thrown error, just
garbage that happens to still be in-bounds. Confirmed on FFVI (SNES)'s
AKAOSNES V4 driver: after a harness's own JS-side pre-relocation of a
song's track-pointer table, letting the real "load song" handler's own
`delta = 0x1C24 - romBase; pointer += delta` step run unmodified corrupted
every pointer (values like `0x30BD` appeared where a real, in-range ARAM
address was expected) — the real relocation step was traced byte-exact
only *after* the corruption was already observed, not predicted in
advance.

**Fix, when the harness genuinely needs its own custom placement** (e.g. a
packed/compacted layout that doesn't fit the real transfer's own
byte-for-byte addressing scheme): don't try to skip or patch out the real
relocation code — that risks missing some other side effect it has.
Instead, **feed it an input that makes its own computed correction exactly
zero** (here: overwriting the header's own `romBase` field with the real
driver's own confirmed relocation-target constant, so `delta = target -
romBase = 0`). This lets the real code execute unmodified and produce a
true no-op on top of the harness's already-correct values — real code
staying in the loop, with the harness controlling the outcome through its
inputs rather than through selectively disabling driver logic.

Before trusting any harness-side pre-relocation as final, check the
target's own docs (or trace forward from the bypassed entry point a short
way) for whether the real code re-derives addresses from a base/delta
computation of its own — if the format has any per-instance "assembled
against an arbitrary base, corrected at load time" convention (common for
overlay/relocatable resource formats generally, not just SPC700 audio
drivers), assume it does until traced otherwise.
