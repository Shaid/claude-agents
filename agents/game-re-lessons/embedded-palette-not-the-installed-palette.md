# A file's embedded palette is not proof that the game installs it

**When it bites:** a container format carries its own palette in its own
header, you parse it correctly, every file renders as plausible art, and
you're about to call the colours confirmed — without having traced what the
loader does with those palette bytes *after* the read.

Finding the palette and parsing it correctly answers "what is in this
file". It does not answer "what colours does this file appear in", and on
hardware with one global colour-register bank those are different
questions by construction: several assets composited onto one screen
physically cannot each use their own palette. Somebody's palette wins. A
per-file embedded palette is a perfectly ordinary way for an *authoring
tool* to ship art, and the runtime is free to ignore it.

The shape to look for is a loader that reads the header palette into a
**single shared global scratch** and leaves the decision to the caller.
Confirmed on Phantasie III (Amiga, `nicodemus`): `loadCmp()` at file offset
`0x1264` does `Read(fh, palScratch /* DATA+0x2AEE */, 0x20)` for *every*
`.cmp` it opens — one fixed destination, overwritten by the next load.
Callers then either install it immediately, copy it to a per-screen slot,
or do nothing. `loadBanks()` (`+0x7F64`) loads all seven monster/party
sprite banks and copies the scratch to a per-bank slot for `i == 0/1/2`
only; of those three slots, **only slot 0 (`heros.cmp`, `DATA+0x2BCE`) is
ever passed to the palette setter**. Slots 1 and 2 have exactly one
reference each in the whole executable — their own store. Banks 3-6 aren't
copied out at all. So all seven banks display under `heros.cmp`'s palette,
and six files' genuine, correctly-parsed header palettes are dead data.

Cost of not checking: the project had rendered `giant1.cmp` as a purple
dragon and a blue giant, eyeball-verified as "plausible game art" and
documented as confirmed. The real game shows a grey-blue dragon and a
green giant. 36,487 wrong pixels out of 384,000 across the six banks.

**Cheapest first move — count callers of the platform's palette-install
primitive, before tracing any individual file's loader.** The whole
question collapses if that primitive has one call site: every palette the
game can possibly display passes through it, so enumerating *its* callers
gives an exhaustive per-screen table instead of a per-file guess. Here
`graphics.library/LoadRGB4` had **exactly one** caller in 175 KB
(`setPalette` at `+0x11D6`), with no `SetRGB4` and no direct `$DFF180`
write anywhere in the binary — 13 call sites of `setPalette`, and the map
was complete. Equivalents worth counting first on other platforms: SNES
CGRAM DMA setup, PSX `LoadImage` to the CLUT region, VGA `0x3C8`/`0x3C9`
port writes.

**"Written but never read" is load-bearing here, so build it root-based**
(see `negative-from-addressing-root-not-shapes.md`) — and note this
binary mixes absolute-with-relocation *and* A4-relative small-data
addressing, so completing only one root would have left a silent hole.

**Verification needs a control group, or you've only found the reference
tool's bug.** The oracle here was a third-party sprite viewer's published
PNGs. Six sprite banks matched at **0 mismatches out of 384,000 pixels**
under `heros.cmp`'s palette. That alone is equally consistent with "the
reference tool just always applies one palette" — an artifact, not a game
fact. What discriminated it: four *scene* `.cmp` files the same site
publishes matched at **0 mismatches under their own header palettes**, and
forcing `heros`' palette onto them broke them badly (55,591 mismatches on
one). A blanket rule would have been wrong; the bank-specific rule the
disassembly predicted is what the reference actually obeys. Whenever a
reference render disagrees with your decode, find a same-format subset the
reference gets right under the *old* rule and confirm your *new* rule
leaves it alone — a positive plus a same-format negative control is what
separates a discovered rule from a copied mistake.

Related but different failure modes: `palette-storage-quirks.md` (where a
palette *lives*), `shared-scratch-copper-list-palette-patch.md` (a
copper-shaped byte run that is stale scratch, not anyone's table),
`same-name-cross-port-colour-mismatch.md` (a sibling port is ground truth
for structure, not necessarily for colour).
