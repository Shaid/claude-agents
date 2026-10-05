# A patch/override layer keyed by numeric archive entry id can hold the table you want under a generic filename no semantic name search will ever match

**When it bites:** about to write "no patch-layer / update / DLC copy of
table X exists anywhere in this project's dumps" on the strength of a
filename search (`item`, `weap`, `scenario`, the table's community name)
over an override tree whose own index is **numeric** — a LayeredFS-style
`INFO0.bin`/manifest that maps `entryId -> path`, a per-entry override
table, anything where the base archive's directory index is the join key.
Also bites in reverse: an already-found override file named `fixed_data.bin`
/ `data.bin` / `common.bin` that nobody has opened because the name says
nothing. **And in a third direction — the manifest as a naming oracle:** a
band of anonymous, numerically-addressed archive entries whose subsystem is
unknown, guessed, or mis-labelled, when nobody has checked whether the
override layer names *any* id in or near that band (see the second case
below).

## What happened

Fire Emblem: Three Houses (`chimera`): a prior pass needed the v1.2.0 patch
copy of the `WeaponData`/`ItemData` table to prove a DLC weapon was filled
into a reserved slot. It ran an exhaustive case-insensitive filename search
for `item`/`weap` across all four update layers (`patch1`-`patch4`) and all
six DLC titles' extracted archives — 0 hits — and concluded "no
`fixed_itemdata.bin`-equivalent exists", then built a whole "inferred from
two sibling tables but never observed" write-up on that negative, with the
byte-exact proof marked as a gap "pending a more complete dump".

The file was in the dump the whole time. The override layer is
`patchN/INFO0.bin`: 288-byte records `{u64 entryId, u64 decompressedSize,
u64 compressedSize, u64 isCompressed, char path[256]}`, keyed by the base
archive's **DATA0 entry index**. The weapon table is DATA0 index **6**, and
entryId 6 in `patch4/INFO0.bin` points at
`rom:/patch4/nx/data/fixed_data.bin` — a name with no semantic content at
all (its siblings are `fixed_persondata.bin`, `fixed_classdata.bin`, which
is exactly why the search assumed a `fixed_itemdata.bin` would exist).
Walking INFO0 by `entryId <= 45` (the whole gamedata range) listed every
patch copy in seconds; diffing entry 6 against base DATA0[6] then gave the
missing byte-exact proof (largest identical-filler group 280 -> 277: slot
190 = the DLC weapon, plus two more).

## Second case — one overridden id names a whole anonymous band

Same game, same `INFO0.bin`, opposite use. FE3H's body/combat motion had
never been located; a pass looking for it found 21 structurally-identical
archives at `DATA0[4253..4273]` (17-slot packs, one nested slot full of
`_A2G` clips) and, on rig-size clustering alone, wrote them up as the
per-class combat movesets — a plausible, entirely wrong classification that
then drove a fruitless search for a class -> archive index function.

Dumping `patch4/INFO0.bin` and simply asking "does any id in 4240-4290
appear here?" returned exactly one row: `entryId 4271` ->
`rom:/patch3/nx/action/motion/KB_M18_0.bin.gz`. One name settled two things
at once. The band is `nx/action/motion/`, and `M18` (plus rigs of 34-143
bones, versus the humanoid 56) makes it **per-creature** motion, not class
motion. The very same manifest dump listed the real class-motion containers
ten entries later — `4622..4632`, `KB_L_100_PACK.bin` ... `BC_PACK.bin`,
whose clips use exactly the 56-bone humanoid core.

The move is cheap enough to be a reflex: whenever a numerically-addressed
archive band's *purpose* is in question, dump the override manifest sorted
by `entryId` and read the neighbourhood. A single overridden entry is
enough, because patch layers override individual files, not subsystems — and
one real path names the directory, the naming convention, and usually the
sibling containers you actually wanted.

## The rule

When an override/patch mechanism is addressed by the base archive's own
numeric index, enumerate it **by the table's id**, never by name:

1. Find the table's base-archive index (you already have it — it is how the
   master loader opens the file, e.g. `mov w2,#6 ; bl open_by_index`).
2. Walk every override manifest for that `entryId`, ignoring `path`.
3. Only then look at what the path is called.

A filename search over such a layer is not a negative — it is a null
result about naming conventions. Contrast
`dlc-content-ships-as-loose-named-file-not-archive-slot.md` (the opposite
direction: content that *left* the numeric index and is now only
name-addressed); together they say the join key changes per layer, and the
search has to use whichever key that layer actually uses.
