# A vtable-bridged consumer is invisible to every direct-call census — xref the data table's own address, and read compute-then-compare validators as free vtable-slot oracles

**When it bites:** a value's producer (a table-walker, a resolver returning
an id) and its suspected consumer (an archive/model/resource loader) cannot
be connected by any `bl`/call-target census in either direction — the
producer's callers all look like UI/predicate code, the consumer's callers
all pass "unrelated" values — on a C++/OO-era binary (console generations
from PSX onward, any engine with class hierarchies).

Two censuses that are individually exhaustive (a from-scratch
capstone/objdump `bl`-target scan AND a full Ghidra xref walk, run
independently and agreeing exactly) can both be structurally blind to the
one link that matters: the value crosses between subsystems as a **virtual
getter on a shared object** (`blr [vtable + K]`), which no direct-branch
census can see. Confirmed on Fire Emblem: Three Houses (`chimera`, Switch,
ARM64): multiple full passes proved the outfit-table resolver `FUN_3F390`'s
return value "never reaches" the archive loader — its 8 callers only
classify or discard it — while the loader's own callers passed "unrelated"
ids. The real bridge: the appearance-descriptor class exposes the modelId
as virtual getter `[vt+360]` (one binding is a thin
marshal-args-and-tail-call wrapper around `FUN_3F390`), and the model-part
request functions read it back with `blr` and feed it to the loader.

**What finally cracked it, in order of leverage:**

1. **A plain, unfiltered xref scan on the DATA table's own address** — the
   producer walks a hardcoded table; scanning all of `.text` for
   `ADRP+ADD/LDR` pairs landing anywhere inside the table's byte range
   (with the already-known reader as positive control) surfaced a sibling
   function cluster no pass had ever seen. Multiple sessions had xref'd
   functions extensively but nobody had xref'd the table itself. Run this
   FIRST when a data structure's consumers are in question — it is
   immune to call-graph blindness.
2. **Compute-then-compare validators name vtable slots for free.** A
   function that recomputes a value fresh (calling the real producer) and
   then asserts equality with a virtual getter (`bl FUN_3F390; …;
   blr [x8+360]; cmp; b.ne fail`) is the code's own statement that
   `[vt+360]` returns exactly that value — a semantic oracle for the slot,
   with no class-hierarchy reconstruction needed. Grep any candidate
   validator/refresh functions for this shape before attempting full RTTI
   or vtable mapping.
3. Function pointers found via a data scan for function-start offsets
   (relocation-applied images may store them base-0, not VA-based — check
   one known pointer's raw bytes before scanning) locate the vtables and
   registration tables that complete the picture.

**Fix:** treat "no call path connects producer and consumer" on an OO-era
binary as a statement about *direct branches only*, never as evidence the
link doesn't exist. Before writing that negative: xref the shared data
structure's own address; scan for the producer wrapped in thin
vtable-shaped functions (marshal + tail-call); and look for equality
assertions between a fresh computation and a virtual call.
