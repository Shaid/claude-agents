# Before decoding a "template/preset table"'s field-by-field content, byte-dump it at rest — it may be pure runtime scratch state with nothing authored in it

**When it bites:** a struct/table is repeatedly read AND written by several
different pieces of code (several rooms' scripts, several draw routines),
each accessing it through the same selector/index scheme, and the working
hypothesis is "a bank of author-provided presets" (colors, rectangles,
sizes) that the game selects between — with the open task framed as
"decode the table's full field-by-field content" or "map every slot's
meaning." Before spending more effort tracing every consumer to build that
field map, dump the table's **raw bytes directly from the static
(decompressed-but-unexecuted) disc image**, at every selector/index value
the code uses, on every disc/build the project has. If it's all zero, the
"authored content" premise is refuted outright, not just unconfirmed.

## What went wrong (and the decisive check)

On Valkyrie Profile (PSX, `valkyrie`), two structures shared by several
rooms' GPU-effect code (a portrait/dialogue panel, ambient rectangles, a
rotating-ring effect) were named a "GPU overlay TEMPLATE bank" across two
earlier investigation rounds, because multiple independent consumers all
read colour/position fields out of them through the same selector byte —
exactly the shape you'd expect from a small bank of author-chosen visual
presets. The open item was framed as "decode the tables' remaining
field-by-field content" (a handful of word offsets were already mapped out
of ~277 and ~28 possible slots).

A direct hex-dump of both tables' raw bytes, at both selector values the
consuming code actually uses, on both shipped discs, showed **every single
byte was zero**. Widening the check to the surrounding memory region found
the two tables sit inside one unbroken ~6 KB zero-run in the decompressed
static image — a run that also contains several OTHER globals the project
had *already* independently confirmed were runtime-only state (a GPU
primitive cursor, a small runtime pointer array, several flag bytes). That
combination — genuinely all-zero at rest, embedded among known-runtime-only
neighbors, in a region a decompressed overlay image can cheaply zero-run
compress — is decisive: there is no authored content in these tables at
all. They are shared, double-buffered **scratch** state that the consuming
code populates fresh every time it runs, computed from each caller's own
script parameters, not a preset bank. This didn't just narrow the open
question — it *dissolved* it: "decode the full field content" was never
achievable, because there was never any content sitting there to decode.
The already-built structural field maps (which offset each consumer reads
or writes) remained the real, final ceiling.

## The generalizable technique

This is a distinct, cheaper cousin of
`relocation-invariant-content-across-copies-proves-placeholder.md` (which
needs two independently-relocated copies of a resource and a *predicted*
address-dependent delta to falsify a pointer field). This technique needs
neither: it applies to **any** struct suspected of holding authored preset
content, using only:

1. The table's confirmed base address(es) and stride (from disassembling
   its consumers — you need this regardless, to know where to look).
2. A direct byte-dump of the table from the game's own static, at-rest
   image (a decompressed overlay, a ROM bank, a decrypted executable
   section) — not from a runtime memory capture, and not inferred from
   what consumers *write* into it during play.
3. A check of whether it's all-zero (or a single repeated filler byte), and
   if so, how far that zero-run extends on either side — a large run
   shared with other already-confirmed runtime-only globals is strong
   corroboration this is a real BSS-style scratch region, not a decode
   accident or truncated extraction.

Run this check **before** investing further effort building an exhaustive
per-consumer field map for "template content" — if the table turns out to
be all-zero, that per-field map is still useful (it tells you which offset
each consumer reads/writes), but the framing shifts from "what preset lives
in slot N" (unanswerable — nothing does) to "which runtime code writes/reads
offset N, and when" (the real, complete answer). Getting this backwards
costs a full investigation round spent hunting for content that was never
authored in the first place.

**Companion active technique: disassemble the record's own allocator for a
`memset`-style call, not just the byte-dump above, when the question is
"does this field default to zero for the field's WHOLE lifetime" rather
than "is it zero in the samples I checked."** A byte-dump at rest proves
the field is zero in whatever snapshot you took; it doesn't prove the field
is *deliberately, unconditionally* zeroed on every allocation, which
matters when the open question is specifically "is there a writer we
haven't found, or does this field just default to zero." Same Valkyrie
Profile companion-array investigation, a later round: rather than treat
"the field defaults to 0" as an unprovable assumption alongside "or some
other overlay writes it," the record's own allocation site was
disassembled directly — the allocator call (`jal <task-pool-allocator>`)
was immediately followed by a call to the project's already-confirmed
resident `memset` equivalent, with the record's own pointer, a literal
fill-byte of 0, and a literal length matching the record's exact byte
stride. That's direct, byte-exact proof (not inference from a snapshot)
that the WHOLE record — not just the one field — is zeroed unconditionally
before any individual field write, closing the "maybe it just isn't
written yet in my sample" half of the question outright. **Fix:** when a
"who writes field X" search comes up empty, check the record's own
allocation/init code for a bulk-fill call before concluding the negative is
inconclusive — a fill-byte-0/length-matches-stride call there is a stronger
and cheaper proof of deliberate zero-default than any number of additional
consumer-side searches.
