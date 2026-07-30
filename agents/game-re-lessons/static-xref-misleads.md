# Static xrefs to data can mislead you two ways

**When it bites:** you've found a code xref to a data region and are about to declare it "the reader/renderer" — or a jump table's static bytes look like garbage and you're about to discard the finding.

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
