# A game can have real, working `public/assets/<game>/` output and still be invisible in the shared multi-game viewer

**When it bites:** wiring a newly-decoded game's assets into a
seer-framework project's shared asset viewer (`tools/viewer/`) for the
first time — the extraction/build scripts run fine and write correct
output under `public/assets/<game>/<platform>/`, but the viewer's
game/platform `<select>` never lists the game at all, with no error
anywhere.

## What went wrong

Frontier: Elite II (Amiga, `hunter` project) already had a fully-decoded
3D model format, a verified submodel-assembly pipeline, and real OBJ/PNG
output under `public/assets/frontier/amiga/` from prior sessions — but the
game had never been added to `src/game-id.ts`'s `GAME_IDS`/
`GAME_DISPLAY_NAMES` or `tools/shared/game-config.ts`'s `GAME_CONFIGS`.
The viewer's game/platform selectors are populated entirely from
`public/assets/games.json`, which is written by `writeGamesManifest()`
iterating `GAME_CONFIGS` — a game with real assets on disk but no entry in
that array simply never appears as an option to select, and there is no
error message anywhere in this path (the viewer just shows the other
games, as if this one didn't exist).

## The fix

Before assuming "write correct assets and the viewer will pick them up"
for any game that hasn't shipped through this viewer before, check both:

1. `src/game-id.ts` — the game's id must be in `GAME_IDS` (and ideally
   `GAME_DISPLAY_NAMES`).
2. `tools/shared/game-config.ts`'s `GAME_CONFIGS` — needs an entry with
   `assetDir` matching the directory name under `public/assets/` (the
   viewer computes `ASSET_BASE` as `/assets/<id>/<platform>` directly from
   the id, so id and `assetDir`/directory name must agree). `supported:
   false` is fine for a game whose extraction stays bespoke scripts
   outside the shared `runPipeline`/`buildAssets` mechanism (the existing
   convention for several games in this family) — it only affects whether
   `npm run extract-data` drives extraction, not whether the viewer lists
   the game.

After adding both, regenerate `public/assets/games.json` by running the
project's real entrypoint as a module (`npx tsx tools/extract-game-data.ts`
or the project's `npm run extract-data`) — not an ad hoc `npx tsx -e
"..."` inline eval importing the same module, which can fail to resolve a
`file:`-linked workspace package's exports map in an eval context even
though the same import resolves fine as a real module entrypoint.

This is a distinct failure mode from
`step-runs-standalone-but-not-pipeline-registered.md` (an *existing*
game's `buildAssets` function not wired into its own already-present
config entry) — this one is the game having **no config entry at all**,
one level higher up.
