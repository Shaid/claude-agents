# A single short-magic hit inside compressed/encrypted/high-entropy data is expected noise until you check the bytes after it

**When it bites:** a corpus-wide byte-pattern search for a short (3-5 byte)
magic/tag string (a codec fourcc, a container magic, a chunk tag) returns a
small number of hits — especially just one or two — somewhere inside a
region you already know is compressed, encrypted, or otherwise high-entropy
(an LZO/LZ-family payload, an unbroken cipher stream, packed executable
code), and the temptation is to report it as a real, if unconfirmed, find.

**The statistics make this predictable, not surprising.** A specific N-byte
ASCII/binary pattern is expected to recur by pure chance roughly once per
`256^N` bytes of uniformly-distributed data. For a 4-byte magic, that's
about once every 4 GB. Scanning a few GB of genuinely high-entropy content
(compressed payloads, encrypted blocks) and finding *one* hit for a 4-byte
magic is not evidence of anything — it's within the expected noise floor.
Confirmed on NieR (2010, PS3, `flower` project): a corpus-wide search for
CRI's `CRID` (Sofdec/USM video) magic across ~3 GB of full raw-content
scanning turned up exactly one hit, inside a still-undecoded
`"lzo"`-tagged, LZO-compressed `.MDP` background-pack file. Reported alone,
that reads like a real lead toward a whole undiscovered video codec.

**Fix: never report a short-magic hit as a finding without checking the
bytes immediately following it against the real target format's actual
header shape.** A genuine container magic is never bare — it's followed by
a predictable, low-entropy structure (a length/size field with a plausible
small-to-medium value, a version/type byte, reserved zero padding). In the
NieR case, the bytes right after the `CRID` hit were
`1B 20 89 22 5C 66 7C 80...` — high-entropy garbage with no resemblance to
USM's real chunk shape (a real `CRID` chunk is followed by a BE `u32` chunk
size and a small padding/type byte). That one check reclassified the hit
from "unconfirmed lead" to "refuted, pure coincidence" in under a minute,
and let the negative conclusion stand without an asterisk. This generalizes
past MPEG-PS pack headers (already covered for the "noisy 4-byte pattern,
only trust with other structural evidence" case) to *any* short magic
search that includes compressed/encrypted regions in its scan surface —
frame the result as "how many hits does pure chance predict for this
pattern length over this many scanned bytes," and actively falsify any hit
at or below that rate against the real format's structure before writing
it up either way.
