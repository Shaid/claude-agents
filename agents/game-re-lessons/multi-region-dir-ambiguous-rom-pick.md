# A second same-extension ROM in the data directory silently hijacks file selection

**When it bites:** a project's `loadRom()`-style helper finds "the" ROM file
in `data/<game>/<platform>/` by extension match (`*.sfc`/`*.smc`/`*.rom`/...)
with no further check, and a second release of the same game (a different
region, revision, or a JP/US/EU comparison pair) is dropped into that same
directory — before trusting which file a pipeline run or test suite actually
loaded, or before adding a second regional dump to an existing data directory
at all.

A single-ROM-per-directory assumption is baked into most first-pass loaders:
`readdirSync(dataDir).find(f => /\.(sfc|smc)$/i.test(f))` returns whichever
file the filesystem lists first. That's stable enough while only one file
ever matches the pattern, so it ships without anyone noticing the assumption.
The moment a second same-extension file lands in the same directory — e.g. a
"how similar is the Japanese original" comparison task drops
`Final Fantasy IV (J).smc` next to the already-confirmed
`Final Fantasy II (USA) (Rev 1).sfc` — the helper picks one of the two with
no signal about which, and every existing test/pipeline call downstream
keeps passing (or fails in a confusing, indirect way) depending purely on
`readdirSync`'s listing order, which is not guaranteed to be alphabetical and
was never a design choice in the first place. In the case that surfaced
this, listing order happened to still favor the correct (US) file only
because "Final Fantasy II" sorts before "Final Fantasy IV" — pure
coincidence, not a real guard.

**Fix**: make ROM selection content-addressed, not listing-order-addressed.
Compute CRC32 (post-header-strip) for every candidate file matching the
extension pattern, match against an explicit expected-CRC32 allowlist for
the release you want, and require exactly one match; fall back to "the only
candidate present" when there's just one file, so an unidentified/modified
dump still loads without a hard failure. Give the two releases distinct
loader entry points (e.g. `loadRom()` for the US CRC set, `loadJpRom()` for
the JP CRC set) rather than one function with a region parameter threaded
through every call site. This is cheap to add once (a CRC32 table almost
always already exists in the project for oracle-verification purposes, per
`romhacking-community-tools-first.md`) and turns a silent, order-dependent
pick into an explicit, verifiable one — confirmed fixing exactly this in
`ceres/tools/ffiv/rom.ts` when a JP FFIV dump was added alongside the
already-confirmed US dump.
