# `Buffer.concat(parts)` copies bytes at call time — mutating a `parts[i]` buffer afterward silently never reaches the result

**When it bites:** hand-building a synthetic binary test fixture (Node.js
`Buffer`, e.g. following the `kt-rdb.test.ts`-style convention of composing
a format's real byte layout from named sub-buffers instead of vendoring
copyrighted game data) where some header field's value — a `size`, a count,
an offset — depends on the *total* length of pieces appended after it, so
the natural code shape is: allocate the header buffer, push it into a
`parts` array, append the rest, call `Buffer.concat(parts)` to get the
final bytes, *then* go back and write the now-known field into the header
buffer.

That last step does nothing. `Buffer.concat` allocates a brand-new buffer
and copies every input buffer's bytes into it **at the moment it's called**
— the returned buffer shares no memory with its inputs. Writing into
`chunkHeader` (or any `parts[i]`) after the `concat()` call mutates a
buffer nothing downstream ever reads again; the concatenated result keeps
whatever `chunkHeader` held *at concat time* (typically all-zero, straight
from `Buffer.alloc`).

## What happened

Chimera (`asrs-ktsr.test.ts`, testing a real, already-shipped decoder for
FE Warriors: Three Hopes' ASRS audio container): a fixture builder wrote a
chunk's `type`/`soundId`/`flags`/offset fields into a `chunkHeader` buffer
*after* calling `const chunkBody = Buffer.concat(parts)` (because the
chunk's own `size` field — the total span including the header — could only
be computed once `chunkBody.length` was known). Every write after that line
was silently lost. The resulting fixture's `size` field (and every other
header field) read back as `0`.

This didn't produce an obvious crash. The real decoder's chunk-walking loop
has a legitimate guard (`if (size <= 0) break`), so the malformed fixture
just made the parser return **zero sounds** with no exception — a
plausible-looking "the format doesn't apply here" result rather than a
visible error. Finding the actual cause needed temporarily adding debug
logging inside the decoder's (correct, intentional) catch-all "skip
malformed chunk" block to confirm no exception was even being thrown there
— the bug was entirely upstream, in the test's own fixture construction,
not in the decoder under test.

## The fix

Write every field whose value is known *before* concatenation into the
sub-buffer while it's still the live object referenced in `parts` — that's
safe; mutations up to the moment of the `Buffer.concat()` call are fully
captured. For the one or two fields that can only be computed *from* the
concatenated length (a whole-chunk `size` field being the common case),
patch them directly into the **returned** buffer after concatenation
(`chunkBody.writeUInt32LE(chunkBody.length, offset)`), never back into the
original sub-buffer. If more than one such late field exists, prefer
computing every size/offset value from a running cursor *before* any
`concat()` call at all (as `kt-rdb.test.ts`'s existing fixture helpers do)
so no post-concat patching is needed in the first place — it's less error
prone than remembering which specific late-write path is still safe.

This is a generic Node.js `Buffer`/`TypedArray` semantics gotcha (`.slice()`
shares memory with its source; `Buffer.concat()`/`Array.from()`/spread do
not) — not specific to this format or project. It will bite any future
synthetic-fixture builder in any seer project that follows the
"allocate-then-patch" pattern across a `concat()` boundary.
