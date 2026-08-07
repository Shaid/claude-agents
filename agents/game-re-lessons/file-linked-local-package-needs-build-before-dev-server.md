# A `file:`-linked local package (e.g. a `seer/packages/*` dependency) can 500 a consumer's dev server until it's explicitly built once

**When it bites:** `npm run dev` (or any Vite/esbuild dev server) fails
every request with `Failed to resolve import "@some-scope/some-package"` for
a dependency declared as `"file:../other-repo/packages/some-package"` in
`package.json` — especially right after a fresh checkout/worktree of either
repo, or after pulling upstream changes to the sibling package. The game
viewer's category selectors/search box silently stay empty (no error
visible in the UI at all) because the whole module graph failed to load,
not because of any data/manifest problem — don't start debugging the
manifest or pipeline output before checking the dev server's own log.

A local `file:` dependency (the seer framework's `@seer/*`/`@seer-project/*`
packages are exactly this shape) is a **source** package, not a published
build artifact — its `package.json` declares `"main": "./dist/index.js"`,
but nothing automatically produces `dist/` just because `node_modules/`
contains a symlink to the source directory. If that sibling package has
never been built in this environment (a fresh clone, a fresh worktree, or
simply a machine that never ran its `npm run build`), `dist/` doesn't
exist, and Vite's import resolution fails outright — the consuming
project's own `npm install`/`npm test`/`tsc --noEmit` can all be totally
clean, since none of them actually load the dependency's runtime code, only
type-check against `.d.ts` files that may or may not exist either.

**A second trap on top of the first**: TypeScript's incremental project-
reference build (`tsc -b`) can report a project "up to date" from its
`tsconfig.build.tsbuildinfo` cache even when the `dist/` output that cache
describes doesn't actually exist on disk (e.g. `dist/` was `.gitignore`'d
and never committed, but the `.tsbuildinfo` file was, or is stale from a
different machine/path). Running `npm run build` in that case appears to
succeed instantly but produces nothing — `rm` the `.tsbuildinfo` file (or
pass `--force`) before trusting an "up to date, 0 files changed" build.

**Fix, confirmed on the `flower` project's `@seer-project/audio-ui` (which
itself depends on `@seer/core`, both hit this)**: `cd` into the sibling
package's real source directory and run its own `npm run build` (deleting a
stale `tsconfig.build.tsbuildinfo` first if the build claims "up to date"
with no `dist/` present), then restart the dev server. `dist/` is normally
`.gitignore`'d in these packages, so this never touches version control —
but every fresh environment (new clone, new worktree, CI) should expect to
need it once.
