# A file newly written into `public/` while `npm run dev` is already running 404s as a silent 200 (SPA fallback), not a visible error

**When it bites:** an offline pipeline run writes new files into
`public/assets/...` (or any other `publicDir`-served path) while a Vite dev
server from an *earlier* shell session is still up, and a subsequent
Playwright/`curl` check of the new file returns **HTTP 200** but the body
is the app's `index.html` shell, not the expected content — easy to
misread as "the file is being served, so it's a real content bug in my
pipeline" since the status code alone looks fine. `curl -I` (headers only)
is actively misleading here: it reports `200 OK` with no hint the body is
the wrong document; only inspecting the actual response body (`curl -s`
with no `-I`, or a `Content-Type`/`Content-Length` check against the known
expected value) reveals the SPA-fallback substitution.

**Root cause:** Vite's dev server (`appType: 'spa'`, the default) falls
back to serving `index.html` for any request path it can't resolve to a
real file, exactly like a production SPA host would for client-side
routing — but its static-file resolution for `publicDir` appears to use a
directory listing/stat snapshot that doesn't pick up files created *after*
the server process started, at least for freshly-created subdirectories
under `public/`. A file that already existed before the server started
(or an existing file that gets its *contents* overwritten in place) serves
correctly; a brand-new file — even in an already-existing directory — does
not, until the dev server is restarted. Confirmed on a `flower`-project
pipeline run: `public/assets/devilmaycry/ps2/textures/tim2_capcom.json`
(freshly written that run) 200'd with the `index.html` shell body every
time, while `public/assets/devilmaycry/ps2/textures/tim2_capcom.png`
(same directory, same run) served correctly — the only difference being
file extension is a red herring; the real difference was whichever files
existed in that exact leaf directory before the dev server's own process
started. Killing and restarting the dev server (no code change) fixed it
immediately, confirmed by re-`curl`ing the identical URL.

**The fix / workflow rule:** after running (or re-running) any pipeline
step that writes new files into `public/`, **restart** any already-running
`npm run dev` process before Playwright-verifying the result — don't trust
"the dev server is already up, no need to restart" just because it was
serving fine before the pipeline run. A `200` status alone does not prove
a static file served correctly on this dev server; check the body/
`Content-Type` too when a "file exists on disk but viewer can't load it"
symptom shows up right after a fresh pipeline run.
