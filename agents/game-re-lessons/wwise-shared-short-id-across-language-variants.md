# Wwise localized voice lines share one numeric ID across languages — dedup-by-ID silently drops whichever language loses the race

**When it bites:** extracting Audiokinetic Wwise audio (`.wem`/`.bnk`) from
a game with per-language directories (`English(US)/`, `Japanese/`, etc.),
and the output-naming scheme dedupes/keys assets by their numeric Wwise
"short ID" alone.

## What went wrong

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

## The fix

Fold a locale tag into the output name whenever a Wwise-sourced audio asset
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

## The general lesson

Don't assume "same numeric ID across two directories" always means either
"duplicate, safe to dedupe" or "distinct, needs no rule" — check which one
applies to *this* ID space specifically, per content type. A container
format's own legitimate content-sharing convention (asset variants that
really do re-embed the same bytes) and a middleware's legitimate ID-reuse
convention (language variants that deliberately share an ID while differing
in content) look identical from the outside — both are "the same ID appears
more than once" — but need opposite handling. Wwise's whole
language-bank-switching design guarantees the second case for any
per-language directory split; treat it as the default assumption for any
localized Wwise corpus, not an edge case to discover the hard way.
