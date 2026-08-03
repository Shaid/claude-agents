# A shared filename stem doesn't prove two files are paired — byte-diff to check

**When it bites:** a corpus has an obvious naming convention suggesting two
files go together (`foo.hdr` + `foo.dbs`, an index + its payload), and
you're about to reverse-engineer the smaller one *as* a directory/index into
the larger one on the strength of the naming alone.

Wizardry 6 Amiga's `scenario.hdr` (414 bytes) sits right next to
`scenario.dbs` (188980 bytes) — an index-into-payload pairing by every naming
convention in the corpus (`msg.hdr`/`msg.dbs` really is exactly that kind of
pair, confirmed independently). But a systematic byte-diff of `scenario.hdr`
against every same-family `.dbs` file found it has **zero** matching bytes
against `scenario.dbs` — and is instead **byte-for-byte identical, in its
entirety**, to the first 414 bytes of a completely differently-named file,
`newgame.dbs`. The naming convention was a red herring for which file it's
actually tied to.

Before building a decoder that assumes a directory/payload relationship
implied by filename stems alone, run a cheap systematic prefix/full-content
byte-diff of the candidate "index" file against *every* plausibly-related
file in the corpus (not just the one the name suggests) — a full match
against an unexpected file is easy to find this way and easy to miss
otherwise, and it can completely change what the smaller file's role is
(here: a copy of a shared template block, not an index at all).
