# A decompiler's own debug-print label for a field is its fallback formatting, not the field's real semantics

**When it bites:** a community reverse-engineering decompiler/disassembler's
text dump prints an as-yet-unnamed struct/opcode field with a generic
placeholder label (`size:%d`, `unk1:%d`, `param:%d`, `flags:%d`) and it's
tempting to adopt that label as the field's documented meaning — especially
once the decoded value cross-checks byte-exact against real file bytes, which
can feel like proof the label is correct too (it only proves the *offset and
width* are correct, not the *name*).

## What went wrong

Cracking Frontier: Elite II's PLANET model-bytecode opcode (`hunter` project,
Amiga), a fresh Python port of `watsonmw/fe2-intro`'s `modelcode.c`
`DecompileModel()`/`Render_PLANET` case correctly decoded every byte-offset
and field width byte-exact against the real executable and the tool's own
text dump. The dump itself printed the field as `size:29765` — the tool's
generic catch-all print format for a plain unlabeled `i16`, used identically
for several other still-unresolved fields elsewhere in the same decompiler.
That label was initially written into this project's own docs verbatim as
"a size field, role unresolved" — reasonable given the decompiler is a real,
buildable, ground-truth-verified renderer, not a guess.

It was wrong. Reading `render.c`'s actual **runtime consumer** of the same
byte offset — `RenderPlanet()`, the function that draws the real graphics,
as opposed to `modelcode.c`'s text-printer that only exists to dump bytecode
as human-readable source — showed the field is read as `i16 radiusParm` and
immediately normalized via `FloatRebase(&baseScale, radiusParm)` against an
exponent seeded from the model header's own scale field. It's the planet's
**radius**, encoded as a mantissa in the renderer's own custom
fixed/floating-point number scheme — nothing like a generic "size."

## The fix

A decompiler's own print label is evidence of nothing beyond "this tool
didn't have a better name for it either" when the label is a generic,
type-only placeholder (`size`, `value`, `param`, `unk`, `flags` followed
just by the raw type/width). Before writing such a label into project docs
as even a tentative semantic name, grep the same reference tool's source
for every OTHER function that reads the identical struct/opcode field —
specifically the real runtime consumer (renderer, interpreter, hardware
register writer), not the tool's own debug/decompile/dump path — and read
what *that* function actually does with the value (arithmetic, a table
index, a normalization call). If the consumer's treatment reveals a real
semantic role, use that; if no consumer exists in the tool at all, label the
field explicitly "role unresolved," not the tool's own print-format
placeholder text, which can otherwise get mistaken for a real name in a
later pass. This is the same underlying discipline as
`reader-side-may-still-be-export-target-math.md` and
`reference-tool-field-never-consumed-by-its-own-importer.md` (a reference
tool's own code-path classification — reader vs. exporter, consumed vs.
unconsumed — is not proof of a field's real-world meaning) applied to a
narrower, very common trap: a *debug-print label specifically*, which reads
like a real field name even though its only job was to make raw bytes
printable.
