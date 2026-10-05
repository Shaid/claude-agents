# A 4-byte "version" field that looks like ASCII digits may need a digit-weighted decode, not a literal string or raw integer read

**When it bites:** a binary format's header carries a 4-byte field that looks
like readable ASCII digits (e.g. literal file bytes `"9200"`, commented
"version" in a community template), and downstream parsing branches on
comparing it to small integer thresholds (23, 25, 30, 11...). Especially
when real decoded values pass individual plausibility checks (small,
sane-looking numbers, no crash) but a byte-exact length/size
self-consistency oracle is available and hasn't actually been run yet.

## What happened

FE Three Houses' G1M `ONUN`/`VNUN` NUN-cloth sections (`chimera`). Every
subsection carries a `GResourceHeader` with a 4-byte `chunkVersion` field
whose file bytes read as plain ASCII digits, e.g. `"9200"`. Two independent
community sources exist for this exact struct: Joschuka/Project-G1M (a C++
Noesis plugin) and the `three-houses-research-team/010-binary-templates`
repo. The C++ source gates its header-skip branches on comparisons like
`if (version < 0x30303330)` — opaque hex literals with no explanation. The
010 template spells out the actual decode as a named helper,
`G1Helper_GetVersionA`:

```
vbase = (version[3] - 0x30) * 1000
      + (version[2] - 0x30) * 100
      + (version[1] - 0x30) * 10
      + (version[0] - 0x30);
```

i.e. **digit-weighted by byte position**, not a literal forward string and
not a raw little-endian `u32` reinterpretation. For file bytes `"9200"`
(byte[0]='9', byte[1]='2', byte[2]='0', byte[3]='0') this decodes to
`0*1000 + 0*100 + 2*10 + 9 = 29` — nowhere near the literal-string reading
(9200) or an LE-`u32` reinterpretation of the same 4 bytes. The C++ tool's
hex constants are simply this same digit-weighted encoding spelled as hex:
`0x30303233` = 23, `0x30303235` = 25, `0x30303330` = 30.

Parsing `chunkVersion` as the literal number 9200 (or as a raw LE integer)
instead of 29 silently selected the wrong version-gated skip branch in a
variable-length control-point/influence array — reading 3D positions from
176 bytes too early. **The resulting floats still looked individually
plausible** (small numbers in a sane range, no exception, no crash) — this
did not present as an obviously broken decode.

## What actually caught it

Not eyeballing the decoded values. A **byte-exact self-consistency check**:
sum every decoded entry's own consumed byte length across the whole array,
and require the total to land exactly on the subsection's own independently
declared size field, with zero slack. The wrong version parse failed this
check outright (way short of the declared size); the corrected digit-weighted
parse landed exactly on it across two independently-sampled real files (a
5-entry array summing to 11,732 of 11,732 declared bytes; a 1-entry array
summing to 864 of 864) — and the decoded values turned out to be physically
coherent chains (parent-index links forming clean parallel trees), not just
byte-accountable.

## The generalizable rule

Before trusting a naive string or raw-integer read of any binary field that
*looks* like readable ASCII text/digits (a "version" tag, a build stamp),
check whether the format's own convention re-encodes it (digit-weighted,
BCD-like, or otherwise non-literal) — especially when more than one
community reference tool exists for the format. One tool spelling the
convention as an opaque pre-computed hex/int literal and a second spelling
it as a named decode function are not independent confirmations of "read it
literally" — cross-check their comparison constants against each other
(reverse the hex literals digit-by-digit) rather than trusting whichever
source is easier to read. And regardless of which reading you pick, run a
byte-exact size/length self-consistency check before calling a variable-length
record decode correct — individually-plausible field values are not
sufficient evidence on their own.
