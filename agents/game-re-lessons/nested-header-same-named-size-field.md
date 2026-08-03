# A nested sub-header can have its own same-named size field that isn't the outer header's

**When it bites:** a two-level header (an outer file header pointing at an
inner directory/sub-header, both of which declare a field with the same or
a very similar name — e.g. both call something `directory_size`) and a
trailer/terminator/bounds check computed from one of them lands a few bytes
short or past a value that should be zero/sentinel — looking exactly like
file corruption on a structurally sound file.

The two same-named fields can describe different spans: the outer header's
`directory_size` may cover the *entire* directory region (sub-header +
tag/entry blocks), while the inner sub-header's own `directory_size` field
(read from the file, not assumed equal to the outer one) covers only the
tag/entry blocks that follow *it*. Using the outer field where the inner one
belongs mis-locates anything computed as `directory_offset + directory_size`
by exactly the inner sub-header's own byte length — small enough to look
like an off-by-a-few-bytes bug in your parsing logic rather than a
misidentified field.

Confirmed on EOB3's GFFI cinematic container (`~/Development/crawl`,
`apps/thirdeye/resources/gffi.cpp`/`.hpp`): `GFFIHeader.directory_size`
(outer, at file offset 16) and `GFFIDirectoryHeader.directory_size` (inner,
read from the file at `directory_offset + 4`) are two distinct stored
values. The format's own trailer-validation rule (`u16` zero sentinel at
`directory_offset + directory_size`) uses the **inner** one — using the
outer field instead raised a `struct.unpack_from` out-of-bounds error on
every real `.GFF` file tested, which read as "the directory is corrupt or
my offset math is wrong" until the two fields were checked against each
other directly and found not to match. Fix: when two nested structures
share a field name, read and use the *closer-scoped* (inner) one for any
offset math relative to that structure, and treat the outer one as
descriptive metadata only unless the format's own reference implementation
says otherwise.
