# Base-path deployment — the gotcha and the fix

Most seer sites so far have gotten their own subdomain (`<project>.shaid.net`),
so `base` stays at the Astro default (`/`) and none of this ever bites. The
moment a site deploys to a **subpath** instead — e.g. GitHub Pages project
pages at `https://<user>.github.io/<repo>/`, so `astro.config.mjs` sets
`base: '/<repo>'` — a real, silent-until-you-look bug shows up: most
hand-authored links and images in the site stop working, but the build
succeeds and says nothing.

Confirmed empirically (build `dist/` with `base` set to a subpath and grep the
output) on the `nicodemus` (Phantasie) site:

- **Starlight's own *generated* chrome is base-aware automatically.** Sidebar
  entries built from `_sidebar.json` slugs, prev/next pagination,
  breadcrumbs, the table of contents, and the `favicon`/`title` Starlight
  config all render with `/<base>/...` correctly. Nothing to do here.
- **Anything a human typed by hand is not — including inside Starlight's own
  frontmatter schema.** A markdown link written as
  `[Graphics Formats](/phantasie/graphics/)`, a raw `<img
  src="/assets/phantasie/amiga/cover1.png">`, a component that builds a path
  as a literal string, *and even* a splash page's `hero.actions[].link:
  /phantasie/` in frontmatter YAML — all render with the **bare**
  `/phantasie/...` or `/assets/...` path in the built HTML, no `/<base>`
  prefix. Don't assume a field is safe just because Starlight owns its
  schema — only chrome Starlight *generates itself* from your content
  (sidebar, pagination, etc.) gets prefixed; anything you typed a path into
  yourself, YAML or JS, doesn't. On GitHub Pages these 404. This is the
  actual bug behind "the site works in `astro dev` but breaks on GitHub
  Pages."

## The three fix patterns

**1. Components and `.astro`/`.mdx` frontmatter script** (anywhere you build
a path with JS): use `import.meta.env.BASE_URL`, but **normalize its trailing
slash — don't assume either way.**

```js
// SpriteGallery.astro, GameCardGrid hero objects, etc.
const base = import.meta.env.BASE_URL.replace(/\/$/, '');
const imagePath = `${base}/assets/${assetPath}/${manifest}.png`;
```

Earlier drafts of this doc claimed `BASE_URL` "always has a trailing slash."
**That's wrong — verify, don't rely on it.** Confirmed against Astro's own
docs (configuration-reference `#base`) and empirically by toggling the config:
`BASE_URL`'s trailing slash is controlled by the separate `trailingSlash`
config option, not by how `base` itself is written or by whether it's `/`
(root) or a subpath. With `trailingSlash` unset (Astro's default,
`"ignore"`), `BASE_URL` mirrors whatever string `base` is verbatim — `base:
'/nicodemus'` → `BASE_URL` = `/nicodemus` (no trailing slash); `base:
'/nicodemus/'` → `BASE_URL` = `/nicodemus/` (trailing slash kept); `base: '/'`
→ `BASE_URL` = `/` (which *is* a trailing slash, trivially). A hardcoded
assumption in either direction breaks depending on how the next person
happens to write `base` in `astro.config.mjs` — normalize instead of assuming.

(You *could* instead pin `trailingSlash: 'never'` or `'always'` in
`astro.config.mjs` to make `BASE_URL` deterministic project-wide and drop the
per-call normalization — but that setting also changes every *generated* page
URL sitewide, e.g. `astro preview`'s own server starts 404ing the
trailing-slash form of every route. That's a much bigger blast radius than
this bug needs and hasn't been verified against real GitHub Pages static
serving — don't reach for it just to dodge a one-line `.replace()`.)

**2. Hand-authored internal links and images anywhere they can't run
JS** — `.md`/`.mdx` prose, *and* frontmatter YAML fields like a splash page's
`hero.actions[].link` — use a **relative path**, not
`import.meta.env.BASE_URL`. Plain `.md`/YAML can't run JS at all, and mixing
conventions page-to-page is its own maintenance trap. A relative path
resolves correctly under any base with zero config-awareness needed —
including in frontmatter fields that belong to Starlight's own schema; being
a Starlight-defined field does not make it base-aware (see above).

Compute the prefix from the page's route depth (number of path segments in
its URL, treating an `index.md`/`index.mdx` as *not* adding a segment):
`docs/phantasie/screens.mdx` → `/phantasie/screens/` → depth 2 →
`'../'.repeat(2)` = `../../` reaches the site root; append the target's full
path from there (`../../assets/phantasie/amiga/cover1.png`,
`../../phantasie/graphics/`). This is not the *shortest* relative form but it
is trivial to get right mechanically and always correct — don't bother
computing the minimal common-ancestor form. For the splash/home page itself
(depth 0, `index.mdx`), the prefix is empty — `phantasie/`, `assets/foo.png`,
not `./phantasie/`.

This is mechanical enough to script in one pass across every content file
rather than hand-editing each occurrence — walk `src/content/docs/**/*.{md,mdx}`,
compute each file's depth from its path, and regex-rewrite `](/…)` and
`src="/assets/…"` to the relative form. Re-run whenever pages move.

**3. The one real trap: markdown image syntax vs. raw `<img>`.** Astro's
built-in markdown pipeline intercepts `![alt](path)` syntax specifically (not
raw HTML) and tries to resolve it as a **locally-imported, build-optimized
asset relative to the content file**. A pipeline-decoded PNG living in
`public/assets/` is not such a file:

- `![alt](/assets/foo.png)` (absolute) — the image pipeline treats a
  leading-`/` path as an already-public URL and passes it through
  untouched... which means it *builds*, but silently skips base-prefixing
  (same bug as above).
- `![alt](../../assets/foo.png)` (relative, "fixed" the way you'd fix a
  link) — the pipeline now tries to import it as a local asset, can't find
  it (it's not in `src/`), and the build **fails outright** with
  `[ImageNotFound] Could not find requested image`.

Neither form is right. **Never use markdown `![]()` syntax for a
`public/assets/` image — use a raw `<img src="...">` HTML tag instead**, with
a relative `src` per pattern 2 above. Raw HTML `<img>` is passed through
untouched by both plain `.md` (CommonMark embedded-HTML passthrough) and
`.mdx` — it never enters the markdown image/asset pipeline at all. If the
page needs `<Lightbox />` or any other component/import alongside those
images, it has to be `.mdx` anyway (plain `.md` can't `import` or render
components); if it's pure prose-plus-images with no component needed, plain
`.md` with raw `<img>` tags works fine too.

## Verification — don't skip this when `base` is set to a subpath

`npm run build` passing with the default/root base proves nothing about this
bug — it only shows up once `base` is a real subpath. Before calling a site
done that deploys to a subpath:

1. Build with the **actual production `base`** set in `astro.config.mjs`
   (not a temporary root override).
2. Grep the built `dist/**/*.html` for `href="/` or `src="/` occurrences that
   do **not** start with `/<base>/` — anything left over is an unprefixed
   hand-authored link or image. Don't stop at content pages: check the
   homepage/splash page too, since that's where `hero.actions[].link` and
   hero-image `src` props typically live.
3. Spot-check that every relative `href`/`src` in the output actually
   resolves to a real file/page when joined against the page's own directory
   (a small Node script doing `path.join(pageDir, href)` and `fs.existsSync`
   catches this in seconds across the whole `dist/`).
4. `astro preview` and curl a few nested pages under `/<base>/...` — and
   confirm bare `/` 404s, since that's the real GitHub Pages behavior too.
