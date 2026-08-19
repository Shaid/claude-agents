# Readable fragments naming an already-known sibling format/container inside an "unclassified" leaf mean it's compressed, not opaque

**When it bites:** a container walk's magic-byte classifier dumps a
sizeable chunk of leaves into an "unrecognized"/"unclassified" bucket
(neither the archive's own recursion magic nor any already-decoded
content-magic matches), and — before writing that bucket off as low-value
raw/opaque data — a byte-level look at a handful of its members turns up
short, clearly-readable ASCII runs that happen to name things this project
*already knows about*: a sibling container's own self-name string, an
already-confirmed magic/tag, a build-tool path fragment, or a literal
byte-for-byte prefix match against an already-decoded header's own first
few bytes. This is much stronger and more specific evidence than "high
entropy" or "looks random" alone (the trigger for
`decoded-random-looking-region-is-compressed-files.md`, which assumes you
already have a directory pointing *into* the blob) and different from
`undecoded-format-may-be-compressed-with-known-codec.md` (which is about a
*specific resource type's* implausible count/periodic-artifact tells, not
a whole unclassified *bucket* of leaves with no known directory at all).

Confirmed on Drakengard (PS2, `flower` project): a full recursive walk of
`IMAGE.BIN` found 662 leaves (81% of the archive's bytes) tagged with an
unfamiliar 4-byte magic (`\0V3a`), correctly left un-recursed since it
matched neither of the archive's own two container magics. A byte dump of
the first ~200 bytes of one such leaf showed high-entropy binary
interspersed with clearly readable fragments: the literal strings
`"tmp_pack.txt.bin"`, `"mmodel"`, `"CJFg"` (this project's own confirmed
skeleton-format magic), a build-tool source path (`"convert\C_ALL\shapA"`),
and — most decisive — a literal 8-byte run `66 70 6b 00 00 00 00 00`
byte-for-byte matching the already-confirmed `fpk` container header's
first 8 bytes (magic + reserved `u32`=0). That's not a coincidence three
different known names would produce; it's the readable-literal-run
signature a byte-oriented LZ compressor leaves behind (uncompressible or
first-occurring text gets copied through mostly intact while match tokens
and binary data around it look like noise). Escalating with exactly this
evidence (the specific strings found, their exact byte offsets, and the
literal-prefix match) let `re-codebreaker` identify the wrapper (a custom
32-byte header around chained LZO1X blocks) and confirm it decompresses to
a real, already-known `fpk` sub-tree — unlocking 3,368 further character/
prop packages that a whole prior session's plan had wrongly attributed to
a miscounted "297 total" figure instead (see
`tracker-prose-is-not-evidence.md`).

**Fix:** when triaging a large unclassified-leaf bucket, don't stop at "no
recognized magic, therefore opaque/low-priority." Byte-dump a handful of
members' full content (not just the first 16-64 bytes most container
probes read) and scan by eye for readable runs. If any name something the
project already has a confirmed format/container/tag for — especially a
literal prefix match against an already-decoded header's own bytes — treat
that as strong evidence of compressed sibling content and a real
escalation candidate, not a dead end.
