# A container field's name can imply the wrong base offset — the resulting garbage looks exactly like an undiscovered second encryption/compression layer

**When it bites:** a directory/TOC record has a field that looks self-
explanatory by name (e.g. `FileOffset` next to a header's own
`ContentOffset`) and every payload it points at, across every file type
sampled, decrypts/decompresses to uniform high-entropy garbage — even
though the *directory/header itself* (the structure containing the field)
decoded perfectly cleanly, with readable self-describing metadata. The
temptation is to conclude there's a second, undiscovered crypto or
compression layer wrapping the actual content, separate from whatever
already-confirmed transform got you the directory.

Before chasing a phantom second layer, question the base-offset arithmetic
itself. A field's *name* is not proof of what it's relative to — some
container formats compute a payload's real position from a *different*
header field than the one whose name suggests it, especially when a format
was clearly retrofitted with an alternate addressing mode (a legacy-
compatibility branch, a mode flag, a size threshold) that a name-driven
reading has no way to know about.

Confirmed on NieR (2010, PS3, `~/Development/flower`)'s CRI Middleware
`CPK` archive: a `Toc` row's `FileOffset` field reads as obviously relative
to the header's own `ContentOffset` field (`ContentOffset + FileOffset`) —
a completely reasonable first hypothesis. Every file that formula located
decrypted to uniform high-entropy bytes across every extension sampled
(PNG icon, plaintext script, plaintext subtitle text, mesh data) — genuinely
indistinguishable from "there's a second, proprietary Cavia encryption pass
on top of the already-solved Sony NPDRM `.SDAT` layer," and was treated as
exactly that hypothesis for a while. The real, publicly-documented CPK
convention (matching CriPakTools'/vgmstream's own readers): `fileOffsetBase
= TocOffset if TocOffset >= 0x800 else ContentOffset` — i.e. the correct
base is usually the *Toc's own* offset, not `ContentOffset`, despite the
field being named `FileOffset` right next to a plausible-looking
`ContentOffset`. Switching the base immediately produced a byte-exact PNG
signature at the expected entry and clean `CRILAYLA`/`@UTF` magic bytes
across a dozen more extensions — there was no second crypto layer at all.

**Fix, and the general test to run before escalating to "there's a hidden
transform":** find (or manufacture) one entry whose decoded content has an
**unambiguous, zero-ambiguity magic-byte signature** (a `PNG`/`RIFF`/`ZIP`
file, a known codec tag) and use it as a byte-exact oracle for the offset
formula itself, trying every plausible base field the header actually
offers (not just the one the target field's name suggests) before
concluding the payload needs a new codec. A directory that decodes cleanly
but whose *payloads* look uniformly encrypted is at least as likely to be
an offset-computation bug against the directory's own already-decoded
fields as it is a genuinely separate transform — check the cheap hypothesis
(wrong base field) before the expensive one (unknown cipher/compressor).
This is the container-format-level analogue of
`indexed-operand-needs-base-provenance.md` (an indexed instruction's
encoding doesn't prove which table it indexes) and
`nested-header-same-named-size-field.md` (two same-named fields covering
different spans) — in all three cases, a field's *apparent* semantic role
from its name/position is not itself evidence; only an independent oracle
(a resolved `LEA`, a nested header's own stored value, a magic-byte match)
settles what it actually means.
