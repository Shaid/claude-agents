# When the game's obvious string-table format is empty of game text, mine descriptive asset/package names instead — with exact-match correlation, not chapter/directory proximity

**When it bites:** need real display names for internal entity/character/
boss IDs (a UE3 `Coalesced.bin`-style serialized-INI, or any other engine's
"obvious" localization/string-table container, decodes cleanly but the
section that *should* hold this game's own text has zero real content —
confirmed by walking every section, not sampling a few); or you're about to
fall back straight to external wiki inference without checking the game's
own asset corpus first.

**The obvious string-table format being empty is not the end of
game-internal evidence — it's one source among several, and often the
wrong one.** UE3 games commonly coalesce only generic engine/editor config
(`Engine.Engine`, `SystemSettings`, `PlayerInput`, ...) into
`Coalesced.bin`; a title's actual gameplay text (subtitles, boss names,
mission text) frequently lives elsewhere — baked into UI/Scaleform asset
*names themselves*, not a lookup table at all. Confirmed on Drakengard 3
(PS3): `Coalesced.bin`'s one localization file that should carry this
game's own text (`Sqex03Game.int`) has exactly 0 sections in all 4 real
variants (main+patch × 2 languages) — but the full ~79,000-entry extracted
asset manifest contains a `boss_font_<name>_en/jp` `Texture2D` naming
convention (a title-card font resource, one per boss fight) that
exhaustively enumerates **10 real boss names** nowhere else in any decoded
data, plus descriptive substrings baked directly into ordinary package
names (`BG14_10_ZEROHOUSE_MAP` for the protagonist's own home map,
`BG20_10_DM_GK_CERBERUS2_START` for a specific creature's encounter
package) — debug/production naming leaking real names into the shipped
build the same way `HUNK_DEBUG` source lines or a raw byte-classification
scan on Amiga can leak names (see `hunk-wraps-non-code-data.md`'s sibling
lessons) — is a broadly useful move on **any** engine's asset corpus, not
UE3-specific: search every extracted name/package string for exhaustively-
enumerated repeating patterns, not just the two or three examples you
already know.

**Critical: correlate a found name to a specific data structure by an
*exact* match, never a coarse proximity signal.** The first correlation
attempt tried "same numeric chapter/directory prefix" (e.g. any asset under
`BG10_*` counts as a candidate for a `BG10_SEA_40_EVENT`-housed name) and
produced dozens of false-positive candidates per name — a protagonist's own
mesh cluster, a shared dragon-companion cluster, and a large shared prop
cluster all appear in *every* chapter, so a loose prefix match trivially
"matches" every name tried and proves nothing. Tightening to **the exact
package/directory string** (the named resource's own housing path must
appear verbatim in the target structure's real package/reference set — not
a capped/sampled subset of it, the full untruncated set) is what
distinguished real hits from noise: it correctly found 3 boss names tied to
single, unambiguous mesh clusters, and correctly produced *zero* false
matches for other names whose only "hit" was a large background-scenery
cluster that happens to touch dozens of unrelated packages (a real,
verified rejection, not an oversight — see the paths-tried table this
lesson's project recorded).
