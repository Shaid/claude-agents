# A decode-script's unconditional `main()` fires as an import side effect

**When it bites:** importing a constant or helper function from another
`decode-*.ts`-style CLI script (to share a palette, a parsed-format
struct, or similar), and seeing confusing double output, a wrong
`Usage: ...` error, or `process.exit()` unexpectedly killing a test run.

Seer-framework pipeline scripts commonly follow a "library logic + CLI
`main()` in one file, called unconditionally at module scope" pattern —
convenient for a single throwaway extractor, but it means the file has an
**import side effect**: pulling in one of its exports (a constant, a
parser function) for reuse in a sibling script or a test also executes
its `main()`, which reads `process.argv` meant for the *importing*
script's own invocation (or the test runner's), and can call
`process.exit()` mid-test-run. This is easy to trip when consolidating
several platform-variant decode scripts that need to share one constant
(e.g. a palette) defined alongside another script's CLI entry point — the
natural refactor ("just import it from there") silently breaks both
sides.

Two-part fix: (1) if a value genuinely belongs to a decode format rather
than to one script's CLI, give it its own small module with no `main()`
at all (cheapest, and the more idiomatic seer split — see how `pic-
format.ts`/`decode-pic.ts` already separate format logic from the CLI
elsewhere in this same corpus); (2) for a script whose *exported
functions* (not just constants) genuinely need to be both CLI-runnable
and importable (e.g. by its own test file), guard the trailing call:

```ts
if (process.argv[1] && import.meta.url === `file://${process.argv[1]}`) {
  main();
}
```

instead of a bare `main();`. Verified this doesn't change CLI behavior
(still runs identically via `npx tsx script.ts ...`) while eliminating
the import-time side effect, confirmed via a full regression pass
(MD5-identical output before/after across every existing generated
asset).

**A weaker half-fix that still bites: a `isStandalone` guard that checks
only a filename *suffix* instead of exact-same-file identity.** Several
seer projects scaffold each game's `export-game-data.ts`/`build-assets.ts`
with `const isStandalone = process.argv[1]?.endsWith('build-assets.ts')`
(or `'export-game-data.ts'`) — this looks like the same guard pattern
above, but checks the wrong thing: any file ending in that same suffix
matches, not just *this* file. It works fine in isolation, and keeps
working right up until a second sibling game's script is wired into the
same shared `tools/shared/game-config.ts` (which imports every game's
`exportGameData`/`buildAssets` functions into one module graph so it can
register them). At that point running *any one* game's script directly
(`npx tsx tools/gameA/build-assets.ts <dir>`) transitively imports every
sibling game's `build-assets.ts` too, and each one's suffix-only guard
also evaluates true — so every sibling's `main()` fires as well, each
reading the same `process.argv[2]` meant only for the invoking script,
and crashing trying to open a different game's data file. Confirmed
reproduced in `kolbold`: running `ddsom`'s `build-assets.ts` standalone
crashed on "no such file: `ddtod.zip`" because `ddtod`'s `build-assets.ts`
main() fired as an import side effect — a bug that had been silently
latent since a *second* game was added to the shared config module, well
before the session that actually noticed it (adding a *fourth* game and
testing its own script standalone). The precise `import.meta.url ===
file://${process.argv[1]}` guard above is required, not merely
recommended, for **any file that will ever be imported by a config module
that also imports its siblings** — which in this project shape is every
per-game pipeline script, from the first one written. When fixing one
occurrence of the weak suffix check, grep the whole `tools/` tree for the
same `.endsWith('...-data.ts')`/`.endsWith('...-assets.ts')` pattern and
fix every sibling script in the same pass — the bug is project-wide by
construction, not specific to whichever file you happened to be editing.

**Confirmed again in a second, unrelated project (`methanoid`)**, and this
occurrence is the clean minimal case: Deuteros was the *second* game wired
into `tools/shared/game-config.ts` (after Reunion), and registering its
pipeline for the first time was what turned Reunion's own already-latent
suffix-only guards into a live bug — running `tools/deuteros/build-
assets.ts` standalone crashed with `ReferenceError: Cannot access
'GAME_CONFIGS' before initialization`, because importing it pulled in
Reunion's `build-assets.ts` too, whose suffix guard matched and fired.
Fixed both games' `export-game-data.ts`/`build-assets.ts` in the same pass
with the exact-identity guard, confirming again that the fix must be
applied project-wide the moment a *second* game shares the config module —
not deferred until a third or fourth game's session happens to notice it.
