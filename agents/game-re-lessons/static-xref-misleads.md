# Static xrefs to data can mislead you two ways

**When it bites:** you've found a code xref to a data region and are about to declare it "the reader/renderer" — a jump table's static bytes look like garbage and you're about to discard the finding — or a debug/label string sits right next to a promising call site and you're about to assume the two are related.

1. **An xref found doesn't mean that code is the consumer.** Two confirmed
   `LEA (d16,PC)` refs to a data region turned out to be an unrelated
   byte-patch write and a plain string-printer, not a renderer. Trace what
   the code *does* with the pointer (read vs write vs char-loop) before
   declaring the reader found.
2. **A confirmed jump table (`LEA table,An` / `JSR (An)`) can be populated
   at runtime**, not stored as static data — its raw bytes will decode as
   garbage even though the dispatch code itself is 100% real. Don't discard
   a jump-table finding just because the static bytes look wrong; the
   deciding test is whether some init routine *writes* into that address
   range at runtime. Cost two full sessions on Carrier Command's
   entity-dispatch table before this was recognized.
3. **Physical proximity between a debug/label string and a call site is
   not evidence they're related** — same failure shape as (1), one layer
   earlier. Wizardry 6 SNES had a build-time asset-label string
   (`"...WIZARDRY6 FACE1 "`) sitting immediately before a `JSL` into a
   resource-loader dispatcher; the natural read was "this call loads the
   FACE1 portrait asset." Tracing the call fully showed it dispatched into
   an unrelated input/joypad-polling subsystem (the handler bit-serially
   read `$4016`/`$4017`, hardware registers with no other use) — the
   string was just a nearby comment, not the call's actual subject. Cost a
   real detour before a separate, unrelated method (a whole-ROM opcode
   byte-pattern scan, see `game-re-tooling/snes.md`'s MVN-scan technique)
   found the real loader. Treat a nearby string the same as a nearby xref:
   a lead to verify by tracing behaviour, not a citation to rely on.
4. **A cited "call site" address can be the string literal's own bytes,
   not a `JSR`/`PEA` target.** A prior pass's filename-table entry cited 4
   "standalone call sites" for `PCFILE.DBS`; disassembling each produced
   `invalid`-decoded garbage. The cited addresses were the file offset of
   the `"PCFILE.DBS\0"` string bytes themselves (plus the CODE hunk's
   header size), not the instruction referencing them. Don't read
   "disassembling here produces garbage" as "this must be data" — first
   confirm what's actually at that address (a one-line string search), and
   if it's a string, find the real call site(s) by searching for
   `PEA d16(PC)`/`LEA d16(PC),An` instructions whose PC-relative target
   resolves to that same address (Wizardry 6 Amiga, `sorcery` — this found
   all 4 real call sites plus the master filename table's own load in one
   pass).
5. **Several string literals stored back-to-back doesn't mean they share a
   consumer.** A static far-pointer array of `char*` values that are
   contiguous in the data segment is often just the compiler's own
   string-literal pool for a source file's consecutive array
   declarations, not a semantically-scoped table with one shared reader.
   Confirmed on Conan the Cimmerian (middilgard project): three combat-menu
   strings ("Overhead", "Full Swing", "Forward Thrust") sat pointer-adjacent
   in a flat array alongside unrelated location-name and help-topic
   strings from other, unconnected source declarations — finding the array
   and its xrefs led nowhere specific to any one menu, because the array
   itself isn't the menu; some other, unfound piece of code presumably
   slices a sub-range out of it by index. Don't assume "these look like a
   themed group and sit next to each other in memory" implies "this
   pointer array is their dedicated table" — verify by tracing what reads a
   *specific, bounded* range of the array, not just that the range exists.
