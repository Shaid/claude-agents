# A byte that ends most sampled lists is not automatically the terminator — census for mid-list occurrence and terminator-less lists before writing "X-terminated"

**When it bites:** documenting a fixed-width record table of variable-length
id/index lists (a costume/part registry, a "which children" list, an
inventory slot list) as "`T`-terminated, `P`-padded" because every list in
the handful of records you hexdumped ends in byte `T` and is followed by
`P`s — especially when `T` is a small integer that is also a valid member of
the id space the list holds.

A small id that *every* record legitimately contains (the base body part, the
default weapon, slot 0/1) tends to be authored last by convention, so in a
short sample it looks like a sentinel. The pad byte is usually the real
terminator, and mistaking the data value for it costs twice: a reader built
on it stops one element early on every list that has `T` mid-list, and an
"index-space" hypothesis gets built on a phantom (here: "the ids index mesh
groups and slot 0 growing by 5 groups shifts the whole space").

**The cheap discriminator, before writing the sentence:** over the whole
corpus, for candidate terminator `T` and pad `P`, count (a) lists where `T`
occurs and is followed by at least one more non-`P` byte, and (b) non-empty
lists (at least one non-`P` byte) that contain no `T` at all. A real
terminator has (a) = 0 and (b) = 0; either count > 0 means `T` is data.
Then check `P` the same way — it should never be followed by a non-`P` byte
within the record.

**Confirmed** on Fire Emblem Warriors (Switch, `~/Development/chimera`) slot-18
costume registries (`u32 count` + `count` x 32-byte entries): a prior pass
documented them as "`01`-terminated, `ff`-padded" from one pack's six
entries. A census of all 282 entries in the 56 multi-block packs found 60
lists with `01` in the MIDDLE followed by more ids and 72 non-empty lists
with no `01` at all — `01` is part id 1 (the slot every hero pack populates,
hence authored last), `0xff` terminates and pads, and part id `p` names pack
slot `p + 3` (725/725 references land on a populated slot).
`docs/fe-warriors.md` § slot-18 correction; `parseFewCostumeRegistry` in
`src/data/formats/fe-warriors-pack.ts`.
