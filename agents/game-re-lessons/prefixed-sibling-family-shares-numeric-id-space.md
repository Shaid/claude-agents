# A prefixed sibling file family sharing a numeric id space needs prefix-matched pairing, not just the trailing digits

**When it bites:** a corpus has several *prefixed* sibling file families
that all share one bare numeric id space (e.g. `sn###`, `snHST###`,
`snPTN###`, `snSTG###`, `snSUB###`), each with its own paired companion
file, and you're about to open "the" companion file for a specific
prefixed file using just its trailing digits — especially when a doc or
module comment describes the relationship in prose ("the paired
`snstr*.bin` file") without spelling out that the companion keeps the same
prefix too.

Fire Emblem Warriors (2017, Switch)'s `common/battle/scenario/` directory
holds five such families: `sn013.bin.gz`, `snHST013.bin.gz`,
`snPTN013.bin.gz`, `snSTG013.bin.gz`, and `snSUB013.bin.gz` all coexist,
and each has its own text companion — `snstr013.bin`,
`snstrHST013.bin`, `snstrPTN013.bin`, `snstrSTG013.bin`, and
`snstrSUB013.bin` respectively. Verifying a worked example tied to
`snSUB013.bin.gz`, the first attempt grabbed `snstr013.bin` (stripping to
"the numeric part" and assuming one shared per-number companion) and
searched it for the expected string — found nothing, which would have
been reported as "the worked example appears fabricated" if the directory
listing hadn't been re-checked and `snstrSUB013.bin` (a completely
different file, holding a completely different battle's text) noticed.
The real string was sitting in `snstrSUB013.bin` at a normal offset, exact
match.

The trap is quiet because **both files exist and both parse cleanly** — a
bare-prefix `snstr013.bin` is a real, well-formed text table for a
*different* battle (`sn013`'s), so a wrong pairing doesn't error or look
malformed, it just produces confidently-wrong "the claim doesn't check
out" evidence. Before trusting a negative result from an assumed
file-to-file pairing in a multi-prefix corpus, list the sibling directory
by the same numeric suffix and check how many prefix variants exist for
that number — if more than one, match the *whole* prefix, not just the
digits, between the file under test and its companion.
