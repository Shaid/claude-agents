# A seer pipeline step script that runs fine standalone can be silently unregistered from the real CLI

**When it bites:** a new/rewritten `exportGameData`/`buildAssets` script
runs correctly and produces real output when invoked directly
(`npx tsx tools/<game>/build-assets.ts <dataDir>`), but running it through
the project's actual entrypoint (`npm run build-assets`, `npx tsx
tools/extract-game-data.ts`) prints `⚠ not registered in config —
skipping` and does nothing — easy to miss if you only ever tested the
direct-invocation path (a natural first step while iterating) and never
ran the real CLI before calling the work done.

The seer pipeline framework (`@seer-project/pipeline`'s `runPipeline`) does not
discover step scripts by filename or convention — it calls
`config.exportGameData`/`config.buildAssets` as **function references
explicitly assigned on the platform's config object** in
`tools/shared/game-config.ts`'s `GAME_CONFIGS`. A `build-assets.ts` written
as a self-contained script (its own `main()`, reads `process.argv`
directly, called unconditionally at module scope) works perfectly when run
directly by `tsx` — but the pipeline framework never imports or calls that
script at all unless something in `game-config.ts` explicitly does
`import { myBuildAssets } from '../<game>/build-assets.ts'` and sets
`buildAssets: myBuildAssets` on the config entry. Confirmed on Drakengard 3
(PS3): a freshly-written `build-assets.ts` exported real texture PNGs when
run directly, but `npm run build-assets` reported "build-assets: not
registered in config — skipping" and produced nothing, because the config
object still had no `buildAssets` field at all.

**The fix**: export the real work as a named function matching the
framework's step signature (`(config: PlatformConfig, dataDir: string) =>
void | Promise<void>`), and register it explicitly in `game-config.ts`.
Keep a thin CLI wrapper at the bottom of the script for standalone
iteration, guarded so it only runs when the file is executed directly, not
when its exported function is imported elsewhere:

```ts
export async function buildMyGameAssets(config: PlatformConfig, dataDir: string) {
  /* real work here */
}

const isStandalone = process.argv[1]?.endsWith('build-assets.ts') || process.argv[1]?.endsWith('build-assets');
if (isStandalone) {
  const config = getGameConfig('mygame', 'myplatform');
  await buildMyGameAssets(config, process.argv[2]);
}
```

**Always do a final pass through the real entrypoint** (`npm run
build-assets`, or whatever the project's actual `package.json` script is —
not just direct `npx tsx path/to/script.ts` invocation) before reporting a
pipeline step as wired up. A step that only works standalone is not done.

Distinct from `cli-script-main-fires-on-import.md`, which covers the
*opposite* problem — an unconditional `main()` firing unwantedly as a side
effect of importing the file for its exports. This lesson is about a step
correctly *not* auto-running on import, but then never being invoked by
anything else either, because it was never registered.
