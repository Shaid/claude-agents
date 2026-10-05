# A cited address failing to fit "the" file you assume it belongs to means you checked the wrong file, not that the citation is fabricated

**When it bites:** re-verifying a disassembly citation (your own prior
session's, or an escalation's) by computing `offset = address - assumedBase`
against the one file/region you already have cached or "obviously" assumed
is the right container, and the offset lands past that file's end, or on a
non-code region, or the exact instruction bytes aren't there — before
concluding the citation is wrong, fabricated, or "unverified escalation
output," check whether you're even looking at the right container.

Valkyrie Profile 1 (PSX): two writer-address citations (`0x8005C74C` for a
skill-level field, `0x8005FC40` for a spell-learning append, both against
base `0x80059EE0`) looked unverifiable — the implied file offsets exceeded
the size of the group-directory *region* the checking session assumed held
the code (that slot family's "type 4" region, by analogy with this
project's general "type 4 = raw MIPS code" convention elsewhere). This
produced a confident, well-evidenced-*looking* Correction block declaring
both citations unverified escalation output, published as a commit.

The real bug: the checking session was looking at the wrong TOC slot **and**
the wrong region type. A corpus-wide blind scan — pattern-search the whole
disc image for the container's block-start magic (not just the slots
already cached), decompress every hit, and word-scan each for the *exact*
cited instruction bytes (with a light provenance heuristic — e.g. "is the
base register set by an `addu`/`addiu` within the last N instructions" — to
suppress coincidental matches) — found the exact instruction, byte-for-byte,
in a *different* TOC slot (off by one index from the citation) and a
*different* region type (`type 18`, not `type 4`) than the ones already
sitting in the local cache. Disassembling at the real location reproduced
the *entire* originally-cited instruction sequence — including a 5-global
gate structure spanning dozens of instructions — verbatim. The citation had
been correct the whole time; only the re-verification's search scope was
too narrow. This required a second commit retracting the first "correction"
once the real location was found.

**Fix, generalized:** when a cited address doesn't fit the file/region you
already have on hand, that is evidence about *your* search, not about the
citation's truth. Before writing "unverified" or "doesn't fit any cached
file," run the citation's exact instruction bytes (or a short surrounding
sequence) through a corpus-wide blind pattern scan — most game containers
have some raw magic/header pattern a blind scanner can key on regardless of
which logical slot/entry a byte range officially belongs to — rather than
trusting the container's own declared directory/TOC to enumerate every
place that instruction could physically live. This is strictly stronger
than the file-specific check and costs little more once the scanning
infrastructure exists (a few thousand candidate blocks decompress and scan
in well under a minute in practice). Only after a corpus-wide scan comes up
empty should a citation be downgraded to unverified.
