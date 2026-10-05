# A record array's validation sentinel may only apply to a leading sub-region, not every record

**When it bites:** a repeating record array is really two (or more)
differently-encoded regions concatenated back to back — e.g. a "textured"
prefix carrying a constant marker/sentinel value in some field, followed
by an "untextured" (or otherwise differently-typed) suffix that reuses the
same field for real, variable data with no marker at all — and a parser
validates that sentinel across the *whole* array instead of just the
region it actually applies to.

Confirmed on Parasite Eve (PSX)'s actor-model primitive array: textured
quad/triangle records carry a constant `(0x80,0x80,0x80)` neutral-tint
sentinel in their leading RGB bytes (a GPU convention meaning "use the
texture's own colour, don't tint it"), but untextured quad/triangle
records immediately after them reuse those same three bytes for a real,
variable per-face RGB colour. A parser that required the sentinel on every
record in the array — not just the textured prefix — rejected every real
model that had any untextured faces (most of them). The parser didn't
crash or report an error: it silently fell through to the *next* directory
entry, which happened to also parse successfully (a different, unrelated
model with no untextured faces), and returned that one mislabeled as the
first model. The wrong result looked entirely plausible — a real model
with a "reasonable" total primitive count from elsewhere in the same
corpus — which is what made this dangerous rather than merely broken.

**The fix generalizes:** when a header declares a record array is split
into sub-counts by type/region (e.g. `nTexturedQuads, nTexturedTris,
nPlainQuads, nPlainTris`), any structural check meant to validate or
discriminate one sub-type (a sentinel value, a fixed high bit, a
must-be-in-range field) must be scoped to exactly that sub-type's index
range — never applied uniformly across the whole array on the assumption
that "it's one homogeneous record type with a shared prefix." A parser
that silently accepts the *next* plausible candidate on rejection is
itself a red flag: prefer failing loudly (throw / return null and stop)
over falling through to "the next thing that happens to also validate,"
since a silent fallback converts a scoping bug into a silent wrong-answer
bug instead of a visible one.
