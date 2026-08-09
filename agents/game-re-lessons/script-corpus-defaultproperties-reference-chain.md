# A decompiled scripting-language corpus's own object-reference literals can name-resolve a domain object — stronger than string-mining, but don't trust a numbering coincidence in place of it

**When it bites:** you have a working decompiler for a game's own scripting
VM (UnrealScript via UELib, or an analogous bytecode/script language for
another engine) and need to identify which specific asset/mesh/table a
named game object (a boss, an item, a level) actually uses — especially
after asset-name string mining (title-card textures, package-name
substrings) and structural techniques (zone-exclusive containment,
bone/joint-set clustering) have already found some names but left others
unlinked.

Confirmed on Drakengard 3 (PS3, `flower`): §24 got a working UELib
decompile of `SQEX03GAME.XXX`'s bytecode (6,747/6,752 functions clean).
Mining that corpus's **class names** for a name census turned up a real,
developer-authored `Sqex03GameModel_Bs<NN>_<BossName>` registry — one
empty stub class per named boss, extending a `Sqex03GamePawnNpc_Bs<NN>_...`
pawn class. That alone gives the boss's internal codename, but not yet
which mesh/package it uses. The actual link came from one step further:
the pawn class's own decompiled `defaultproperties` block contained real
UE3 object-reference literals (`m_xDataEdParam=Sqex03DataGamePawnEdParam
'prm_bs04.pdt_bs04'`) — following that reference to the literal package it
names (`PRM_BS04_SF.XXX`, confirmed present on disc) and listing *that*
package's own internal group hierarchy (`umodel -list`, not just its
top-level export names) found the original developers' own nested
`Package` objects literally named after the actual mesh cluster
(`BS_040`/`BS_042`). This closed 2 of 4 previously-unlinked boss names with
evidence that never left the game's own bytecode/package data — no
external source, no name-string coincidence performed after the fact by
the investigating session.

**The general technique**: once a scripting-language decompiler is
working, don't stop at "the class name tells us the identity" — walk one
more hop. A decompiled class's `defaultproperties` routinely contains
literal `Type'Package.Object'`-shaped references to the actual data/asset
packages that class instance uses. Following that reference to the real
on-disc file and inspecting *its* internal structure (not just whether it
exists) can surface a second layer of developer-authored naming (asset
group/folder names inside the package) that closes the loop from "we know
the boss's codename" to "we know exactly which mesh/texture/table is
theirs." This generalizes past UE3/UELib: any engine with a scripting
layer and object-reference-by-name semantics (a config/property system
that stores `<Type> <Package>.<Object>` strings, or an equivalent handle
table) offers the same two-hop technique once its bytecode/script is
readable at all.

**A second trap, found later**: the reference's `Package` segment
(`prm_bs04` above) isn't reliably a separate file to open — see
`ue3-object-reference-package-not-a-filename.md` for a real case where the
identical reference syntax instead named an asset inlined into the
*referencing* file itself.

**The trap**: don't assume a numeric-id coincidence between two different
naming schemes is itself proof. The class registry's own encounter-order
numbering (`Bs00`..`Bs16`) looked at first like it might map 1:1 onto the
asset corpus's own boss-mesh numbering (`BS_0NN`) — and for 3 of the bosses
checked it did (`Bs04`→`BS_040`/`BS_042`, `Bs10`→`BS_010`, `Bs12`→`BS_060`)
purely by coincidence of digits. But a 4th check falsified the general
rule: `Bs09` (a real, independently-confirmed boss, Galgaliel) maps to mesh
object `bs_030`, not `bs_090` — two completely independent numbering
schemes (one a chronological/encounter-slot index, the other an
asset/model-kit id) that happen to agree on some values and disagree on
others. The technique that actually worked was following the real
object-reference chain in every case, not trusting the digit pattern —
treat a numbering coincidence as a hypothesis to verify via the reference
chain, never as the evidence itself, even after it's held true a few times
in a row.
