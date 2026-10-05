# UnityPy's `MeshHandler` reads a vertex channel's correct struct type but skips fixed-point normalization for `UNorm8`/`UNorm16`

**When it bites:** decoding a Unity `Mesh`'s skin weights (or any other
`UNorm8`/`UNorm16`-formatted vertex channel — color, packed UVs) via
UnityPy's `helpers/MeshHelper.py` `MeshHandler`, and a downstream glTF
export fails `ACCESSOR_WEIGHTS_NON_NORMALIZED` (weights should sum to
~1.0) or otherwise shows suspiciously large integer-looking float values
(65535, 255, ...) where a normalized `[0,1]` value was expected.

## What went wrong

Fire Emblem: Engage (Unity 2020.3.18f1, `chimera` project) ships skin
weights as vertex channel format `kVertexFormatUNorm16` (format code 4).
`MeshHandler.read_vertex_data()` correctly identifies this format and
unpacks it with the right struct type (`enums/VertexFormat.py`'s
`VERTEX_FORMAT_STRUCT_TYPE_MAP` maps `UNorm16` -> `"H"`, an unsigned
16-bit integer) — but that's where it stops. It hands back the **raw
integer**, not `raw / 65535.0`. A real weight of `1.0` comes back as the
literal integer `65535`; a real quad like `(0.736, 0.167, 0.096, 0.0)`
comes back as `(48248, 10965, 6322, 0)`.

This is easy to miss because nothing crashes: the values are plausible
enough (integers in a sensible-looking range) to pass through unnoticed
until something downstream actually checks the invariant (glTF's weight-
sum validator did). `MeshHandler`'s own consumer (`export/
MeshExporter.py`'s OBJ writer) never emits weights at all, so this bug has
no in-library symptom to catch it — see
`reference-tool-field-never-consumed-by-its-own-importer.md` for the
general shape of "a reference tool's untested code path is silently
wrong."

## The fix

Read the real channel format directly rather than trusting `MeshHandler`'s
unpacked value as final: `mesh.m_VertexData.m_Channels[12].format` (index
12 is `BlendWeight` for Unity >= 2018; index 2 for earlier versions — see
`assign_channel_vertex_data`'s own channel-index table). Map the format
code to a divisor (`UNorm8` -> 255.0, `UNorm16` -> 65535.0 for the modern
`VertexFormat` enum, or 3/5 respectively for the pre-2019 `VertexFormat2017`
enum) and divide every raw weight by it. **Do not apply this to
`BlendIndices` (channel 13)** — those are genuine integer bone indices and
must stay unscaled; only the weight channel needs fixed-point
normalization. `Float`/`Float16` channel formats (codes 0/1) are already
real floats and need no scaling at all.

**General principle:** a library that correctly identifies a field's
*storage type* has not necessarily applied that type's full *semantic*
contract (here: `UNormN` implies "divide by the max representable value,"
not just "read N bits"). Verify a decoded value's *range*, not just that
the read didn't throw, especially for any field a validator downstream
will check an invariant on (sums to 1, unit length, etc.).
