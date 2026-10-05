# Localized asset variants share one relative-path/ID key across languages — dedup-by-key silently drops or conflates whichever locale loses the race

**When it bites:** extracting audio, textures, or any other asset family
from a game that ships one or more per-locale archives (Wwise `.wem`/`.bnk`
under per-language directories; a whole second/third/fourth CPK/PAK/archive
per language sharing the base archive's own internal relative paths), and
the output-naming/publish scheme dedupes or resumes by numeric ID or
relative path alone, with no locale identity folded into the key.

## Confirmed twice, two different container families

### CPK archive-relative paths (13 Sentinels / Unicorn Overlord, Switch, `vanille`)

Both titles ship a base CPK (`ROBO_US.CPK`, `Unicorn.CPK`) plus 4-5
per-locale sibling CPKs (`ROBO_{FR,GE,IT,SP}.CPK`,
`Unicorn_{DE,ES,FR,IT,US}.CPK`). The locale CPKs reuse the base CPK's own
`.ftx` relative paths almost 1:1 — measured 56-58/57-58 of 13 Sentinels'
locale `.ftx` entries and 14/14 of Unicorn Overlord's overlap the base
CPK's paths, **and** the locale CPKs share those same paths with each
other too (every `Unicorn_{DE,ES,FR,IT,US}.CPK` carries the identical 14
relative names). The shared texture publisher deduplicated/resumed purely
by CPK-relative path (a `Set<string>` of already-published source names,
no CPK/locale identity in the key) — feeding a locale CPK's entries through
it unmodified would have silently skipped every locale texture as
"already published" by the base CPK's pass, and later locale CPKs would
have skipped earlier ones' textures too. Fix: fold a locale tag into both
the dedup/publish key and the sibling Stage-1 data-table output paths
(`locales/<code>/` namespacing) — see `tools/shared/switch-game-assets.ts`,
`tools/shared/switch-cpk-textures.ts`'s `sourcePrefix` param.

### Wwise numeric short IDs (Astral Chain, Switch, `chimera`)

Astral Chain (Switch) ships voice audio under language-named subdirectories
(`sound/English(US)/vo_*.bnk`, `sound/Japanese/vo_*.bnk`). Wwise's runtime
language-switching model works by keeping the **same numeric short ID**
for a "sound object" across every language variant — the engine loads
whichever language's bank is active and resolves the ID against it, so a
localized line's English and Japanese takes are *deliberately* the same ID
pointing at *different* audio content (different voice actor, different
waveform). Confirmed on `vo_em01ff.bnk`: 11 of its 16 embedded short IDs
are byte-identical between the `English(US)` and `Japanese` banks.

An extraction stage that dedupes output filenames purely by numeric ID —
the same convention that is *correct* for this same game's texture
containers, where a duplicate ID really does mean byte-identical re-embedded
content (see the "DAT / DTT pairing" correction in a sibling doc) — silently
drops one language's entire take whenever IDs collide. For this bank, all
16 Japanese lines were skipped as "already written" by the English pass
that ran first; the game's Japanese dub was invisibly reduced to zero
output for that character's whole voice bank.

**The fix:** Fold a locale tag into the output name whenever a Wwise-sourced audio asset
sits under a language-named path segment — derive it from the directory
(`English(US)` → `_en`, `Japanese` → `_ja`, etc.) and append it to the
numeric ID before deduping. Content that is *not* under a language
directory keeps deduping by ID alone (this doesn't do harm — a check
across this same game's non-`.bnk` loose `.wem` streams found 0
English/Japanese filename collisions there, because those *are* stored as
genuinely separate per-language files rather than one shared-ID bank).
Verify the fix by picking one confirmed-colliding ID and checking the two
locale-suffixed outputs are non-identical (different SHA1, not just
different filenames) — a same-hash pair after the fix means the "different
content" premise itself needs re-checking for that specific ID, not that
the fix is wrong.

### CPK archive-relative paths, a new resource type (13 Sentinels, Switch, `vanille`)

The same CPK-relative-path sharing confirmed above for 13 Sentinels'
*textures* also holds for its **sprite models**: each of the 4 locale CPKs
(`ROBO_{FR,GE,IT,SP}.CPK`) carries 22 `.mbs` files, and all 22 exist at the
identical relative path in the base `ROBO_US.CPK` too (22/22 overlap,
confirmed by listing both archives' `.mbs` entries) — the same
"language directory"/"sibling locale archive" pattern generalizes to any
resource type inside a shared-path locale archive, not just audio or
textures. Fixed the same way: the model publisher
(`tools/shared/switch-cpk-models.ts`) takes the identical `sourcePrefix`
parameter as the texture publisher, so this needed no new mechanism, only
reusing the existing one for a second content type.

## The general lesson

Don't assume "same numeric ID/relative path across two archives or
directories" always means either "duplicate, safe to dedupe" or "distinct,
needs no rule" — check which one applies to *this* key space specifically,
per content type, by measuring real overlap (a quick probe script listing
both archives' entries) rather than assuming. A container format's own
legitimate content-sharing convention (asset variants that really do
re-embed the same bytes) and a locale-variant convention (language/region
copies that deliberately reuse the base's own ID or path while differing in
content) look identical from the outside — both are "the same key appears
more than once" — but need opposite handling. A shipping title's
locale-split archives (whether that's Wwise's per-language directories or a
whole second/third CPK/PAK per region) reliably fall in the second bucket:
treat locale-variant reuse of the base's own key space as the default
assumption for any localized corpus, not an edge case to discover the hard
way — and when it's a fresh archive/path-keyed publish cache (not just a
numeric ID), the fix is the same: fold the locale into the key before it
ever reaches the dedup/resume check.
