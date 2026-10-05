# A pointer that gets `free()`-d right after use cannot be the persistent resident table it structurally resembles

**When it bites:** a register holds a pointer to a buffer whose field
layout matches (or strongly resembles) an already-confirmed, persistent,
resident/global resource — and the natural next step is to conclude "this
register IS that resource" and move on, without checking what else the
same function does with the register.

## The trap

Field-layout resemblance is evidence of *shared record format*, not of
*shared identity*. Two different buffers can legitimately share a struct
layout: a persistent, engine-maintained global table, and a private,
transient copy of the same on-disc source data that some unrelated routine
loaded fresh into scratch heap to feed a one-time computation. Nothing
about the bytes read distinguishes them — only what the surrounding code
does with the pointer's *lifetime* does.

## Confirmed case

Valkyrie Profile (PSX, `valkyrie`, round 190): a build routine loops over a
32-byte-stride, 612-record source array reached through register `$s2`,
producing a compact 3-byte-per-item runtime table. The source record's
field offsets (`+0x19`, `+0x1c`) matched the project's own already-
confirmed, persistent `itemTable32` resident table exactly (§ 5's
`classMask`/`field1c` fields) — tempting the conclusion "`$s2` ==
`itemTable32`'s resident pointer (`ctx->word[0x35c]`)." But `$s2` is set
from the build function's own **2nd argument** (`addu $s2,$a1,$zero`, a
plain parameter, not a load from any global/resident address), and
immediately after the build loop finishes, the SAME function calls the
resident `free()` (`jal 0x8001336c`, `a0=$s2`) — the exact deallocator
paired with the `malloc()` (`0x80013104`) used earlier in the same
function for the *destination* table. A persistent, engine-maintained
global would never be freed by one of its own transient readers; only a
caller-owned, caller-allocated temporary staging copy would be. The pointer
holds `itemTable32`-*shaped* data, but it is not `itemTable32` — it's a
private, disposable copy the (unresolved) caller loaded fresh from the
same on-disc source, purely to feed this one conversion pass.

## The rule

Before asserting "register `R` IS resident/global resource `X`" on the
strength of field-layout agreement alone, check what happens to `R` for
the rest of the function: is it ever passed to a deallocator paired with
an allocator seen earlier in the same function (or the same call chain)?
If so, `R` is a temporary, and the layout match only tells you the two
resources share a *format*, not an *identity* — a real, useful, but
different finding. This generalizes past PSX/MIPS: any platform with a
recognizable heap allocate/free pair (PSX BIOS `malloc`/`free`, a
`New`/`Delete` C++ ABI pair, a `Kernel::Alloc`/`Free`) gives this same
cheap, decisive check for free once the pair is identified once in a
project — and it runs in the opposite direction too: a pointer that
survives to a function's `jr $ra`/`RTS` with no matching free, while a
sibling candidate register in the same function IS freed, is itself
evidence for which of two candidates is the persistent one.