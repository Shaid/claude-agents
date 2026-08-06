# A large `build/cache/` from a full-corpus pipeline run can crash `npm run dev` outright, and `server.watch.ignored` may not save you

**When it bites:** `npm run dev` (Vite) dies with `Error: ENOSPC: System
limit for number of file watchers reached` (a native `fs.watch`/inotify
crash, not a normal Vite error message) right after a full-corpus offline
pipeline run has populated a large `build/cache/<game>/...` staging
directory — i.e. right when you go to verify a change in the browser
(Playwright or manual) after a big extractor pass has run.

Root cause: Vite's dev server recursively watches the whole project root
by default. A `build/cache/` staging directory holding a full corpus's
worth of an external tool's intermediate output (umodel export staging,
in the confirmed case — 146,581 files, 36 GB from a Drakengard 3 full
mesh/texture pass) is deep inside the project root and gitignored, but
that doesn't stop Vite from trying to watch every file in it. The OS's
per-user inotify watch limit (`fs.inotify.max_user_watches`, sometimes
generous — 524288 in the confirmed case — but still finite) gets
exhausted, and the whole dev server process crashes, not just a warning.

The obvious fix — add `server.watch.ignored` to `vite.config.ts` pointing
at the offending directory — **did not work** in the confirmed case
(Vite `8.2.0`, a rolldown-vite-based rewrite), tried as both a glob-string
array (`ignored: ['**/build/**']`, and an absolute-path + `/**` suffix
variant matching the pattern Vite's own `emptyOutDir` ignore-list uses
internally) and a predicate function
(`ignored: (path) => path.includes('/build/')`) — neither stopped the
crash, despite reading the vendored `resolveChokidarOptions` source and
confirming the option should merge into the watcher's ignore list. Root
cause of *why* the option didn't take effect wasn't further isolated
(possibly a rolldown-vite-8-specific bug, given how new/different that
rewrite is from mainline Vite+esbuild) — don't assume a config-level fix
that reads correctly in the source will actually work without testing it
against the real crash, and don't sink much time re-trying variations of
the same `ignored` config once one form has already failed.

**Working workaround**: temporarily relocate the big cache directory
outside the project root for the dev-server session (`mv` is instant if
staying on the same filesystem, since it's a rename not a copy), move it
back afterward. No pipeline step reads back its own staging directory once
promotion to `public/assets/` is done, so this is safe. A more permanent
fix worth trying in a future session: move the offline pipeline's staging/
cache directory outside the project root entirely at the config level
(most seer-framework projects' `game-config.ts` controls this path), so
the problem can't recur regardless of Vite version or `ignored` behavior.
