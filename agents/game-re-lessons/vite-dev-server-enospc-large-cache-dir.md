# A large `build/cache/`/`public/assets/` from a full-corpus pipeline run can crash `npm run dev` outright — root cause and a proven fix

**When it bites:** `npm run dev` (Vite) dies with `Error: ENOSPC: System
limit for number of file watchers reached` (a native `fs.watch`/inotify
crash, not a normal Vite error message) right after a full-corpus offline
pipeline run has populated a large gitignored generated-output tree
(`build/cache/<game>/...`, `public/assets/...`, `dist/`) — i.e. right when
you go to verify a change in the browser (Playwright or manual) after a
big extractor pass has run.

> **Correction:** an earlier version of this lesson reported the obvious
> `server.watch.ignored` fix as tried and confirmed **not sufficient**,
> with the root cause "not further isolated," and recommended relocating
> the cache directory outside the project root as the only working
> approach. A later session root-caused the mechanism precisely and
> confirmed a config-level fix with a direct, quantified measurement —
> not just "the crash stopped happening this time." Read on.

**Root cause, confirmed by reading the watcher's own option-resolution
code directly** (`node_modules/vite/dist/node/chunks/node.js`'s
`resolveChokidarOptions` — check this for your own Vite version, these
defaults can change between releases): Vite's **built-in** `ignored`
defaults only cover `"**/.git/**"`, `"**/node_modules/**"`,
`"**/test-results/**"`, and Vite's **own internal** `cacheDir`
(`node_modules/.vite` by default — a completely different, unrelated
directory from any project-specific `build/cache/`). Nothing about a
project's own gitignored output directories (`build/`, `public/assets/`,
`dist/`, `data/`, or whatever a given project calls its staging/output
tree) is excluded by default, even though they're deep inside the watched
project root. Also confirmed: despite being billed as a "rolldown-vite"
rewrite, Vite 8.x's dev-server file watcher is still real chokidar
(`^3.6.0`, confirmed in `node_modules/vite/package.json` and the
`import_chokidar` call site) — the rolldown rewrite replaces the
*bundler*, not the dev-server watcher, so `server.watch` is still
standard chokidar options.

**Measure the real watch count directly instead of trusting "did it
crash this time"** — a dev server's actual registered inotify watches are
readable straight from the kernel:

```sh
for p in $(pgrep -f "vite"); do
  for fd in /proc/$p/fd/*; do
    [[ "$(readlink "$fd" 2>/dev/null)" == anon_inode:inotify* ]] || continue
    echo "PID $p fd $(basename "$fd"): $(grep -c '^inotify' /proc/$p/fdinfo/$(basename "$fd"))"
  done
done
```

Confirmed on Drakengard 3 (PS3, `flower` project): with a real full-corpus
`build/cache/` present (~196K files) and no `server.watch.ignored`
config at all, a dev-server process registered **360,936** inotify
watches — against a `fs.inotify.max_user_watches` of 524,288 (itself
already elevated above the common distro default of 8,192-65,536). One
concurrent process holding its own modest watch allocation, or a
lower-limit machine, tips this straight into `ENOSPC` even without the
corpus growing further.

**The fix that worked, measured**:

```ts
server: {
  watch: {
    ignored: ['**/build/**', '**/public/assets/**', '**/data/**', '**/dist/**'],
  },
},
```

— i.e. **every** gitignored generated-output root a project has, not just
the one that seems biggest. Re-measured the same way after this change:
**104** watches — a 3,470x reduction. Verified beyond the raw count too:
the dev server still starts and serves normally, static file serving for
the now-ignored directories still works fine (`server.watch.ignored` only
affects the *watcher*, not Vite's separate `publicDir` static-file-serving
middleware — the two are different code paths, so ignoring a directory
from the watcher doesn't stop Vite from serving files out of it), and a
full Playwright session (category navigation, search, asset selection)
ran clean with zero console/page errors.

**Honest residual uncertainty**: an earlier attempt at what looks like
the same idea (an `ignored: ['**/build/**']`-shaped glob, an absolute-path
variant, and a predicate-function form) was reported as not stopping the
crash. That earlier attempt's glob was already `**/`-prefixed, so a
missing-prefix theory (chokidar/anymatch anchors an *unprefixed* glob like
`'build/cache/**'` to the string start, but chokidar matches against the
*absolute* resolved path — a real, separately-documented gotcha worth
checking for any glob-shaped `ignored` value that isn't `**/`-prefixed)
doesn't fully explain it. The two most likely explanations, in order of
plausibility: (1) that attempt only ever ignored `build/` and never
`public/assets/`/`dist/`/`data/`, and one of those alone could plausibly
still be enough to tip a large corpus over the limit; (2) it was verified
by re-triggering the crash rather than by a direct watch-count
measurement, which is a noisy binary signal (depends on exact corpus size
and whatever else is concurrently holding watches on the same machine) —
a fix that's real but only *partial* can look identical to "didn't work
at all" under that test. Either way, the actionable lesson holds
regardless of which explanation is right: **ignore every gitignored
generated-output root, not just the one you're thinking about, and always
re-measure the actual watch count directly** (the `/proc` one-liner
above) rather than treating "it happened to not crash this run" as proof
either way.

**Raising `fs.inotify.max_user_watches` is not the right fix here** even
though it's real, standard advice for genuinely large *source* trees
(a big monorepo, a huge `node_modules`) where every watched file matters —
a gitignored, regenerable *build output* tree has no business being
watched at all, and a higher ceiling just delays the same problem while
leaving dev-server startup slower and memory higher than necessary.
