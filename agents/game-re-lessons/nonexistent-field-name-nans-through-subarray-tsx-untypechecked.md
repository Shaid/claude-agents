# A typo'd/nonexistent struct-field name compiles fine under `tsx`, then NaNs silently through `subarray`/`slice`

**When it bites:** writing (or copy-adapting) a `buf.subarray(off + hdr.someField, ...)`-
shaped byte-offset expression against a hand-typed header/struct interface,
where `someField` doesn't actually exist on that type — renamed at some
point, or copied from a similar-but-differently-shaped sibling struct —
especially when the script is run via `tsx`/`esbuild`/`swc` (transpile-only,
no real type-check) rather than through `tsc --noEmit`, and especially when
the resulting failure is *quiet*: no thrown error, just wrong (often
all-zero) decoded output a few calls downstream.

`hdr.someField` on an object whose type doesn't declare it is `undefined` in
plain JS at runtime — `tsx` strips types without checking them, so a field
name that would be a compile error under `tsc` silently passes. `off +
undefined` is `NaN`. The part that actually causes the silent failure is
`TypedArray.prototype.subarray(begin, end)` (and `.slice()`): both convert
their arguments via `ToIntegerOrInfinity`, which maps `NaN` to `0` — not an
exception, not `undefined`, not an empty array. So `buf.subarray(NaN, NaN +
compressedSize)` doesn't throw or return zero-length; it returns
`buf.subarray(0, someNumber)`, a real-looking, valid-length slice starting
from the wrong place. Fed into a decompressor, this can "succeed" and
produce plausible-shaped-but-wrong output, or — as happened here — produce
byte-for-byte all-zero decompressed data with no exception anywhere in the
chain, because the decompressor's own state machine happened to degenerate
cleanly on that particular garbage input.

Confirmed on Valkyrie Profile (PSX, `valkyrie` project): a scratch script's
`decodeSlzAt` helper read `buf.subarray(off + hdr.headerSize, off +
hdr.headerSize + hdr.compressedSize)` — but `SlzHeader` (`tools/shared/psx-
slz.ts`) has no `headerSize` field, only `payloadOffset` (an absolute file
offset, not the header's byte length). `parseSlzHeader` itself reported
perfectly plausible `subtype`/`compressedSize`/`decompressedSize` values (the
header parse was fine), masking that the *payload slice* was wrong. Both
`decodeSlz01`/`decodeSlz02` calls returned all-zero buffers with no error,
which then made `parseVpFont`/`parseVpStringTable` return `null` — several
layers removed from the actual bug. Found by diffing the broken helper
against an already-working sibling script's identical-looking helper
(`verify-voice-collection-character-art.ts`), which used the project's
established literal `off + 16` (SLZ's fixed 16-byte header size) instead of
any header-derived field.

**Fix:** when a header-offset arithmetic expression feeds `subarray`/`slice`,
either (a) run the file through `tsc --noEmit` at least once before trusting
it (a real type-check *does* catch a nonexistent property access, `tsx`
alone doesn't), or (b) add a runtime `assert(!Number.isNaN(offset))` right
before the slice call — cheap insurance against exactly this class of typo
in probe/scratch code that's never going to see a `tsc` pass. When a
decompressor's output comes back suspiciously empty/degenerate with a
clean-looking header parse, check every arithmetic operand feeding the
payload slice against the header type's *actual* declared fields before
suspecting the decompressor itself.
