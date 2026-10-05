# A fan/wiki page's prose algorithm LABEL can be flatly wrong even when its attached reference script is correct

**When it bites:** a community wiki, forum post, or fan-site page names an
undecoded compression/encoding scheme with a specific, well-known algorithm
label ("ByteKiller", "LZSS", "Huffman"...) — especially when that page also
attaches its own script/tool that supposedly implements it — and you're
about to reach for a generic decompressor/library for that named family
instead of reading the attached script itself.

Pool of Radiance (Amiga, `crawl`)'s data files are labelled "ByteKiller 2.0"
on the http://amiga-dev.wikidot.com/project:pool-of-radiance wiki page,
which also attaches a working `pooldata.py` script. Trusting the label first
would have meant reaching for a real ByteKiller decoder (e.g. the `ancient`
library's `ByteKillerDecompressor`) — checked exhaustively against all 843
directory entries in the real corpus, **0/843** pass real ByteKiller's own
12-byte header/XOR-checksum validation. The attached script, meanwhile, is
correct: it's a register-level (`DR[]`/`FLAGS[]`) transliteration of the
game's actual 68000 decompressor — a completely different, custom
backward-reading LZ77 variant with its own embedded checksum — and every
one of the 843 entries decompresses cleanly under it with a passing
internal checksum and exact declared-length match.

**Rule:** when a fan/wiki source both *names* an algorithm and *attaches
working code*, trust the code's own validation logic over the prose label.
Verify the label itself against the *real* reference implementation's own
acceptance check (not just "does the general shape look similar") before
spending effort on a generic tool for that named family — a wrong label
sends you down a real-but-irrelevant decompressor's error messages instead
of at the actual, already-solved algorithm sitting one click away. This is
the compression-specific case of the same general discipline
`community-format-name-mismatches-real-magic.md` documents for container
magics: a community-assigned name is a hypothesis about the bytes, not a
fact about them, checkable the same cheap way (run the *real* thing's own
acceptance/checksum logic against your corpus and count hits) regardless of
whether the mismatch is a magic tag or an algorithm family name.
