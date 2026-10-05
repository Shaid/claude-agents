# A field that should differ between two differently-loaded copies of the same resource, but doesn't, is placeholder/uninitialized-at-rest — not a stride bug

**When it bites:** a project already has two (or more) independently-loaded,
otherwise byte-identical copies of the same code+data resource (a driver,
an engine module) at different memory addresses, and a suspect field in
one copy — believed to hold an absolute memory pointer or other
load-address-dependent value baked in per-copy — decodes to implausible or
garbage-looking content past a handful of clean entries. The instinct is to
keep hunting for a stride/offset/field-width bug in your own extraction.

Confirmed on Millennium 2.2 (Amiga, `methanoid`): a 48-slot instrument/
sample-descriptor table's record format (absolute sample pointer + loop
offset + length + tuning, 12 bytes) was confirmed correct from consumer
disassembly, but slots past the first few (legitimately all-zero,
reserved) decoded to implausible huge/negative "pointers." The game ships
two byte-for-byte-identical copies of the whole driver+data resource,
loaded at different addresses (`mem = file − 0x2D000` vs.
`mem = file − 0x56400`, a `0x29400`-byte delta). Diffing the suspect
table's raw bytes **across the two copies** found them **byte-identical**
— but a real per-copy-relocated absolute pointer, baked in at compile/link
time for that specific load address, would necessarily differ between the
two copies by exactly that `0x29400` delta. It didn't differ at all. That
is decisive: the on-disk content in that region cannot be valid static
pointer data — it must be placeholder/uninitialized-at-rest bytes,
populated by an untraced runtime initialization step, not recoverable from
static file bytes at all. This settled what looked like an open decode bug
as a different, terminal conclusion ("this specific field isn't in the
file"), stopping further time spent hunting for a stride/offset mistake
that didn't exist.

**The general technique:** when a suspect field is supposed to encode
something that provably *must* vary with load address (an absolute
pointer, a relocation-fixed-up value, anything the linker/loader would
bake in per-instance) and the project has two or more independently-based
copies of the same resource available, diff that field's raw bytes across
the copies before re-deriving your field-offset math again. Identical
content where the field's own semantics demand a fixed known delta is
proof the content is stale/placeholder, not a proof of anything about your
decode. This is the address-dependent-content sibling of
`per-instance-file-set-may-be-duplicate-blobs.md` (which uses whole-file
hashing to disprove a per-instance-content hypothesis in general) — this
variant is sharper because it doesn't need a large corpus or an unknown
"is this shared or unique" question: two copies plus one *predicted, known*
delta is enough to falsify "this is real static per-copy data" outright.
