# An unrelocated PIE/NSO image makes every GOT-indirect global read as zero, and a zero looks like a dead end rather than a bug

**When it bites:** disassembling a stripped-but-not-fully-stripped ELF-family
executable (a Switch `NSO0`, or any position-independent executable with a
`.dynamic`/relocation table) straight from a flat image built by a segment-
layout-only loader — one that lays out `.text`/`.rodata`/`.data` at their
declared virtual addresses but never applies the image's own dynamic
relocations. An `adrp`+`ldr` sequence loading a global pointer through the
GOT then reads whatever raw byte the linker left there (typically `0`), and
that zero gets misread as "an opaque/unresolvable global" or "this function
does nothing with this pointer" rather than as an artifact of skipping a
required processing step.

Confirmed on Fire Emblem: Three Houses (Switch, `chimera`): the project's
`buildNsoImage()` (`src/data/formats/nso.ts`) correctly lays out the NSO's
three LZ4-compressed segments at their `memoryOffset`s but performs **no
relocation pass** — its own doc comment says so, framed as a non-issue
("a virtual address read out of the module's own pointers indexes the
returned buffer directly"), which is true only for statically-linked direct
references and silently false for anything reached through the GOT. Two
independent disassembly passes over this exact image — a `ghidra-disasm`
subagent and a separate from-scratch hand-disassembly pass in the same
session — each traced a real call site loading a global via `adrp x8,PAGE;
ldr x8,[x8,#OFF]`, found the loaded value looked like garbage/zero-shaped,
and both **misidentified the two functions built on top of that global**:
one was pattern-matched as a "generic per-field clone/AddRef dispatcher",
the other as a "per-character-id-keyed cache lookup" — plausible-sounding
roles inferred from call shape, not from what the global actually pointed
at. Once the image's `R_AARCH64_RELATIVE` relocations were applied, the
first turned out to be a 4-instruction tail-call thunk into an **allocator
hook table** (unrelated to cloning), and the second a leaf search over an
**unrelated, fixed 60-entry array** with no connection to character ids at
all. Both wrong readings were internally consistent and "looked resolved" —
the zero/garbage value never announced itself as a relocation artifact.

**The fix — apply relocations before trusting any indirect global load:**
for an NSO, the `MOD0` structure at **file offset `0x8`** (a self-relative
`i32` from the `MOD0` tag's own position) points at a small header giving
`.dynamic`'s address; parse `.dynamic` for `DT_RELA`, `DT_RELASZ`, and
`DT_RELACOUNT`, then for every `R_AARCH64_RELATIVE` entry (a real,
`R_AARCH64_RELATIVE`-tagged addend-only relocation — no symbol lookup
needed) write `*(image + r_offset) = imageBase + r_addend` into the flat
image in place, before running any disassembly pass that trusts a loaded
global's value. On this exact binary this was 71,869 entries and unblocked
every GOT-indirect load project-wide (a vtable, an allocator-hook table, and
several other previously-opaque globals all resolved to sensible values in
one pass). Also check for a real `.dynsym`/`.dynstr` at the same time — a
"stripped" executable frequently still exports enough dynamic symbols
(`malloc`, `free`, engine entry points, etc., resolved via the `.rela.plt`'s
`R_AARCH64_JUMP_SLOT` entries) to name call targets directly instead of
guessing from shape, which is a strictly stronger oracle than the pattern-
matching that produced both wrong readings above.

This generalizes past NSO specifically to **any** dynamically-linked,
position-independent ELF-family target (a PIE executable, a `.so`/`.prx`/
similar shared-object container) analyzed via a raw/flat-binary import
rather than a loader that already resolves relocations (a real Ghidra ELF
loader typically does this automatically — this bites specifically when a
project's own hand-rolled segment-layout parser, built to recover the
memory image cheaply without a full loader, is reused for code analysis it
was never designed for). See also the trampoline-role
guessing trap (`trampoline-role-guessed-not-resolved.md`) — this is a
specific, generalizable *root cause* for why that guessing trap is so easy
to fall into on this class of binary: the "target" you'd need to read to
avoid guessing is itself unreadable (reads as zero) until relocations are
applied, so even a conscientious "go read the real target" instinct doesn't
save you without this extra step.
