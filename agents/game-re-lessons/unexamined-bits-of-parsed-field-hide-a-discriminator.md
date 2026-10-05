# A missing discriminator (compression method, format variant, record kind) is often hiding in unexamined bits of a field you already parsed and moved past

**When it bites:** a format needs one more piece of information to resolve
an ambiguity (which compression codec applies, which of several record
shapes this is, which sub-format a block uses) and the search for it
defaults to looking for a brand-new field nobody has read yet — especially
after a field in the same header/record was already parsed, partially
interpreted (a few bits used, e.g. as a boolean or small range check), and
then logged as "rest of the value varies, no confirmed meaning" or
"unconfirmed, not pursued further."

## What happened

Confirmed on the SSI Gold Box "GLIB" container family (`crawl` project,
`docs/goldbox-glib-format.md`): a nested tile-bank sub-container's header
carried a `flags` word that an early pass had already read — just enough to
notice it sometimes took an unusual value (`0x0500`/`0x0501` instead of the
usual `0`/`1`) and to test (and refute) whether that predicted file
corruption. Having answered that one question, the field was set aside as
"varies corpus-wide, no confirmed meaning" while the real blocker (why did
every entry's nested header declare the same impossible total size) was
searched for elsewhere — new byte ranges, new candidate header widths, a
dozen different assumed skip lengths.

The actual answer was in the field already sitting in hand: the HIGH BYTE
of that same `flags` word is the compression method id (`0`=stored,
`3`=10-bit LZW, `5`=byte-oriented LZ77). The "unusual values" that had
already been noticed and dismissed — `0x0500`, `0x0501` — were literally
`5<<8 | 0` and `5<<8 | 1`: method-5 compression with two different low-byte
flags. The discriminator had been staring at the investigator since the
very first pass; it just wasn't recognized as one because the field had
already been "used up" answering a different, narrower question.

## The fix / general rule

When a format needs a discriminator (codec id, variant selector, record
kind) that isn't obviously present:

1. **Re-examine every field you've already parsed for unexamined bit
   ranges**, before scanning for a brand-new field. A byte or word field
   that was read as a boolean, a small enum, or "just flags, doesn't
   matter" often has more bits than the interpretation you gave it used —
   check the full byte/word value, not just the sub-range you first cared
   about.
2. Compute a per-record or per-corpus histogram of the field's *full* raw
   value (not the narrow slice you extracted), split by any independent
   variable you already know matters (per-title constant, per-record
   compressed-vs-uncompressed status inferred some other way, etc.) — a
   clean correlation between the untouched high/low bits and the mystery
   you're chasing is cheap to compute and often decisive on sight.
3. Treat "already investigated, no confirmed meaning" as a note to revisit
   with a sharper question, not a closed door. The field passed one test
   (it doesn't predict X) — that says nothing about whether it predicts Y,
   and doesn't mean every bit of it was examined at all.
4. This is a search-order habit as much as a decode technique: exhaust
   already-parsed real estate before creating new hypotheses about
   undiscovered fields. It's cheaper (no new byte-offset guessing) and it's
   where format designers actually tend to put small enums — bit-packed
   into whatever flags word was already being carried around, not into new
   dedicated bytes.

See `identical-nested-header-across-varying-allocations-is-inert-
boilerplate.md` for the specific format puzzle this technique resolved (a
nested-container header that looked like inert boilerplate turned out to
describe a decompressed image, once the compression method was found this
way).
