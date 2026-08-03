# A whole "undecoded format" may just be reading the compressed bytes with a known codec still in the toolbox

**When it bites:** investigating an unfamiliar/still-open resource format in
a project or engine family that **already has a confirmed compression
codec** used by sibling resource types, and a structural read of the raw
bytes turns up either (a) a "type/version marker" or count-like field whose
observed values are too large or irregular for its presumed role (a marker
that should be a handful of enum values instead ranges into the hundreds; a
"count" that's an order of magnitude bigger than any sibling format's real
object/entry counts), or (b) a periodic/interleave artifact (e.g. "every Nth
byte is junk") whose phase, when tested across many files, is **not locked
to a fixed absolute file offset** — it's uniformly distributed across all N
possible residues rather than concentrated on one.

Both are the signature of reading a compressed stream as if it were the
format itself, not a real structural property:

- A "type/version marker" that's actually the low/high bytes of a
  compressed-size prefix looks exactly like a categorical field with oddly
  many "categories" — because it's really a continuous size value.
- A periodic byte you can't explain ("every 9th byte is junk") that
  **isn't** phase-locked to file offset 0 is very likely an LZSS-style
  flag byte inside a literal run (`[flag][8 literals][flag][8 literals]…`)
  or a similar variable-length codec's framing artifact — its phase is
  wherever the literal run happens to start relative to a flag/tree
  boundary, which has no reason to align with any fixed absolute offset.
  A *real* fixed-stride record field would show one dominant residue, not
  a flat distribution across all of them.

Confirmed on Warriors of Legend's `NECS` scene format (`middilgard`
project): five independent structural approaches across two sessions
(byte-length correlation with no exact stride, a chance-level id-reference
scan, an exhaustive header-field census, an affine regression fit, and the
period-9-interleave observation itself) all failed to decode the format
while reading the **compressed** bytes as the header. `NECS` turned out to
be LZSS-compressed with the exact same `u32-LE-size-prefix + stream`
convention the same project's own `PAMM`/`GAMI`/`LMRF` resources already
used — the "32-byte header with an irregular type/version marker" was the
low/high bytes of the size prefix, and the "period-9 interleave" (already
tested and confirmed *not* globally phase-locked, per the "flat residue
distribution" tell above) was LZSS flag bytes framing the plaintext name's
literal run. Once decompressed, the real format (a 32-byte header + 32-byte
object records + a length-prefixed name) rendered all 316 scenes correctly
on the first attempt.

**Fix:** before trusting any structural reading of an unfamiliar format's
raw bytes, try every compression codec the project/engine family is already
known to use, against a leading size-prefix guess (`u16`/`u32`, LE and BE) —
the same codec is very likely reused verbatim across many resource types in
one game, since games in this era rarely shipped more than one or two
in-house compressors total. This is cheap (minutes) relative to a full
structural investigation (hours to sessions) and should be the *first*
thing tried on any new format in a project that already has one confirmed
codec, not a fallback after structural analysis stalls.

**The lesson generalizes sideways too: after finding this once in a
project, immediately re-audit every other still-open "not compressed"
claim in the same project the same way.** The same wrong assumption (eyeball
the raw bytes, conclude "no compression header" without actually trying the
known codec against them) tends to recur across sibling formats
characterised in the same project/session, since whoever characterised them
made the same unexamined assumption each time. Re-checking Legend's `TAPM`
format's own "no PackBits/LZSS size prefix" claim the same session, purely
on this suspicion, found it was *also* wrong for 37 of 84 resources (the
other 47 genuinely are raw — see `optional-per-record-compression.md` for
this "a minority is compressed, not all-or-nothing" shape). Verify a
compression hit strictly: require *both* an exact decompressed-length match
*and* the decompressor's input pointer landing at (or within 1 byte of) the
compressed buffer's own end — a length match alone can happen by chance on
a capped/greedy decoder.
