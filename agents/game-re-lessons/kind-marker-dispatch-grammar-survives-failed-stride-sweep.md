# A failed fixed-stride sweep doesn't mean a variable-length format resists decoding — try a kind-marker-dispatched grammar next

**When it bites:** a doc records "byte-stride sweep found no fixed record
size that divides evenly" for a format believed to hold a tree/graph/script
serialization (a behavior tree, a scene graph, an event script, any format
whose real content is inherently variable-arity), and the format is filed
as "no fixed structure recovered" or left for escalation on that basis
alone. Also fires in the *opposite*-looking situation: a single guessed
fixed stride (not even a full sweep) decodes record 0 of a list plausibly,
but every record after it looks like a shifted/overlapping window of the
same real bytes rather than obvious garbage — that specific tell (record 0
fine, record 1+ "almost right but shifted") is diagnostic of a variable-
width, leading-type-byte-dispatched grammar, not of a wrong stride number to
keep guessing at.

A failed stride sweep only rules out *one* record model (uniform fixed
size). It says nothing about a genuinely variable-length record stream,
which is the expected shape for tree/graph data in the first place. The
next hypothesis to try, before escalating, is a **kind-marker dispatch
grammar**: read the stream as a sequence of records, each led by a small
integer "kind" field, where different kind values select different record
shapes (some fixed-width with no further fields, some a fixed header
followed by a length-prefixed variable payload). This is forward-walkable
without knowing the shapes in advance — try a handful of candidate shapes
per observed kind value and require the walk to land exactly on an
*independently known* boundary (a container's own declared size, or a
declared element count from elsewhere in the same header).

Confirmed on Fire Emblem Warriors: Three Hopes's `TB1G` "G1BT" behavior-tree
container (`chimera` project, `docs/few-threehopes.md`, `linkdata-g1x.ts`).
A prior pass's stride sweep over `ITBG`'s node-array content (68-18,876
bytes across 44 real instances) found no fixed size — correctly, since real
node records vary 3 to 20+ words. Forward-walking with a 3-shape grammar
(`kind===2`: 3-word fixed record; `kind===3`: 4-word fixed record; anything
else: 6-word header + length-prefixed payload) reproduced the container's
own declared end-of-block boundary byte-exactly for 36/44 real instances —
and, decisively, the header's own separately-declared node count matched
the walk's "long-record" count exactly for every one of those 36. The
semantic domain didn't need a name oracle to trust either: several of the
walk's decoded 32-bit "type hash" values recurred **byte-identically across
all 44 independent instances** (a small, finite, shared per-node-type
constant enum), which is corroboration a random/per-instance field could
never produce by chance.

A cheaper worked instance of the same "record 0 fine, then shifted-looking
garbage" tell, without ever needing to fully crack the grammar: Valkyrie
Profile (PSX, `valkyrie` project)'s title-screen UI-list drawer
(`0x80047070`, a 9-way jump table keyed by each record's own leading type
byte) has variable per-record width — type=1 records are a fixed 16 bytes
(`type@0, id u32@+4, x u16@+12, y u16@+14`), other types differ. A flat
16-byte-stride walk across a whole list decoded record 0 correctly (it
really is 16 bytes wide) but produced garbage for record 1+ that was
visibly just a shifted window of real bytes, not obviously invalid — the
tell that the list isn't uniform-stride at all. Since only each list's own
record 0 was actually needed for the task at hand, the fix here wasn't to
reverse the full variable-width grammar for every type — just to recognize
the shifted-garbage shape as "don't trust record 1+ under this stride," use
the disassembler-confirmed type=1 format for record 0 only, and stop there.

**The general move:** when a stride sweep fails on a format you believe is
tree/graph/script-shaped, don't treat that as "no structure survives" —
build a byte-value classifier (small integer vs. plausible-hash vs.
sentinel like `0xFFFFFFFF`) over the raw word stream, look for a small
integer that reliably precedes either a fixed run of further small values
or a "count, then that many words" run, and forward-walk candidate grammars
against the container's own already-known end boundary. A residual
un-parsed tail (a second, rarer record shape you haven't found yet) is a
much narrower, more tractable remaining problem than "no format exists" —
and is exactly the kind of bounded sub-problem worth a `re-codebreaker`
escalation once two genuinely different grammar hypotheses for it have
failed, rather than escalating the whole format.
