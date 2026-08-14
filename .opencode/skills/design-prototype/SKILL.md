---
name: design-prototype
description: Build a new throwaway Backlog Boss visual-direction prototype (plain HTML/CSS/vanilla JS) that reuses the shared games/app layer. Use when the user asks to create or add another prototype, visual direction, or design candidate for the backlog-boss prototypes — e.g. mentions a new theme like "terminal", "swiss", "calm", "pixel", or says they don't like the current designs and want more options.
---

# Backlog Boss Design Prototype

Add a new visual-direction site to the existing prototype gallery. Sites are
throwaway artifacts used to pick a design direction — never wired into the app.

**Location:** `feature-artifacts/design-prototypes/prototypes/` (gitignored; do
not touch files under `frontend/`, `backend/`, or anything tracked — only ever
write inside the prototypes tree and, if needed, `.opencode/`).

## Gallery today

One shared interaction layer + data set, one directory per site (each site is
self-contained with its own copies), plus an entry gallery:

```
prototypes/
  index.html                     entry point listing every site (add a card here)
  shared/
    games.js                     canonical dataset (window.BB_GAMES)
    app.js                       canonical interaction layer (IIFE, no deps)
    app.domtest.mjs              DOM-shim test ─ run: node shared/app.domtest.mjs
  cockpit/  editorial/  brut/  aurora/         (existing directions)
    index.html  search.html  backlog.html
    styles.css  games.js  app.js                (games.js/app.js are copies)
```

## Workflow

1. **Pick a direction.** Ask the user which new direction they want, or propose
   3–5 that are clearly distinct from the existing four (dark dashboard,
   serif magazine, brutalist, glass/aurora) and from each other.

2. **Scaffold.** `mkdir prototypes/<name>` then
   `cp prototypes/shared/games.js prototypes/shared/app.js prototypes/<name>/`.
   `<name>` must be the same slug used in `data-site` and keep a
   `bb-proto.<name>` localStorage namespace.

3. **Write `styles.css`** implementing the direction, honoring the CSS
   contract below so the shared JS wires up correctly.

4. **Write the three pages** (`index.html`, `search.html`, `backlog.html`)
   reusing the gallery copy, wiring each required `data-*` hook. Mimic an
   existing site's shell (e.g. `aurora/`) for structure.

5. **Add a gallery card** in `prototypes/index.html` (styling: create a
   `.tag--<name>` color in its `<style>` block).

6. **Copy** the real product copy (see below), trimmed to fit the direction.

7. **Verify** (commands under Verification). Do not modify `shared/app.js` —
   tests must keep passing unchanged.

## The page contract (what the shared app.js reads)

Every page body:
`<body data-site="<name>" data-page="home|search|backlog">`

- **home** needs: `[data-stat="active"]`, `[data-stat="completed"]`,
  `[data-stat="hours"]`, `[data-stat="score"]` (empty stat divs), a
  `[data-picks]` mount for the top-3 blended picks, and a
  `[data-toggle-signin]` button for the logged-out preview. Show the
  signed-in and signed-out variations of hero/CTA/user affordance with
  `[data-logged-in]` / `[data-logged-out]` wrappers.
- **search** needs: `[data-search]` text input, a `[data-genres]` chip
  container, a `[data-results]` results mount, `[data-count]`, and a
  `[data-hint]` hint panel.
- **backlog** needs: three sort buttons `<button data-sort="score">`,
  `<button data-sort="time">`, `<button data-sort="blended">`, a
  `[data-refresh]` button, mounts `[data-bblist="active"]` and
  `[data-bblist="completed"]`, counts `[data-count-active]` /
  `[data-count-completed]`, and a `[data-empty]` block.
- **Signed-out preview CSS** (must exist in every stylesheet):
  ```css
  [data-logged-out] { display: none; }
  body.signin-preview [data-logged-out] { display: block; }
  body.signin-preview [data-logged-in] { display: none; }
  ```
- Hidden-state rules the JS relies on: `.hint.is-hidden { display: none; }`
  and `.empty.is-hidden { display: none; }`.

## The CSS contract (dynamic markup the JS renders)

Your stylesheet must style these classes from `shared/app.js`
(`.game-row` children come in this order: index? cover body side):

- `.btn` variants — `.btn`, `.btn--primary`, `.btn--secondary`, `.btn--ghost`,
  `.btn--danger`, `.btn--small`, `.btn--steam`; refresh spinner:
  `.btn.is-spinning::before` with `@keyframes spin`.
- `.game-row` + `.game-row__index`, `.cover` (img, 3:4,
  `.cover.is-fallback` for missing art), `.game-row__body`,
  `.game-row__title`, `.game-row__subtitle`, `.game-row__meta`,
  `.game-row__rating`, `.game-row__sep`, `.game-row__hours`,
  `.game-row__genres`, `.game-row__genre`, `.game-row__side`.
- `.genre-chip` with `.is-active`; `.chip.chip--in-backlog`.
- Toasts: `.toast-stack`, `.toast` (with `.toast--leaving` exit),
  `.toast__message`, `.toast__action`, `.toast__dismiss`.
- Confirm modal: `.modal-overlay`, `.modal`, `.modal__title`, `.modal__body`,
  `.modal__actions`.
- Home stats skeleton: `.stat`, `.stat__label`, `.stat__value` (or whatever
  your design uses — data-stat hooks are what matter).

Covers are resolved at runtime to
`https://cdn.cloudflare.steamstatic.com/steam/apps/<id>/library_600x900.jpg`.

## Data

`shared/games.js` = `window.BB_GAMES` array of `{ id, title, rating, hours,
genres[], platforms[] }`. `id` is the Steam appid (real cover art).
Backlog state lives in `localStorage` under `bb-proto.<site>` (entries:
`{gameId, addedOn, completedOn}`) and `bb-proto.<site>.query` (search text).
It ships with a seeded backlog in `SEED` (12 active, 3 completed) so pages
render the logged-in experience immediately.

## Product copy to reuse (trim or restyle per direction)

- Hero: "Conquer Your Gaming Backlog" / "Stop wondering what to play next.
  Let Backlog Boss prioritize your game library so you can focus on playing."
- Sign-in: "Sign in with Steam"; note: "Your Steam library imports
  automatically. No extra accounts." Preview toggle label: "Preview what new
  visitors see".
- Features: Smart Organization ("Automatically sync your Steam library and
  organize your games with intelligent categorization and filtering."),
  Priority Ranking ("Get personalized recommendations based on ratings,
  playtime, and your gaming preferences."), Track Progress ("Monitor your
  gaming journey and see your progress as you work through your backlog.").
- CTA: "Ready to Take Control?" / "Your gaming library awaits!" /
  "Sign in with Steam and start conquering your backlog today."
- Search: "Discover Games" / "Search the Backlog Boss catalog and, when
  needed, pull fresh Steam game data from IGDB." Hint: "Search by title" /
  "Results include the game name, review score, and time-to-beat when
  available."
- Backlog: "My Backlog", sort labels Score / Time / Blended, button "Refresh
  backlog", sections "On deck" and "Completed".
- Nav labels: Home / Game Search / My Backlog. Footer left:
  "Throwaway prototype · <direction> direction · real Steam data" and a link
  back to `../index.html` ("All prototypes").

## Requirements baked into every site

- Three pages (Home, Game Search, My Backlog) with working nav; real
  recognizable game data; working search + genre filter, score/time/blended
  sort, add-to-backlog, mark-complete with undo toast, remove with confirm
  modal, and refresh-backlog spinner — all provided by the shared app.js,
  so you only style.
- Logged-in experience by default, with the Home-page sign-out preview.
- No Home page as loud as the old billboard hero (keep it restrained).
- Desktop-first but usable when narrow (responsive grid/nav at ~880px, rows
  stack at ~560px).
- Plain HTML/CSS/vanilla JS only — no frameworks, no build step, no network
  besides fonts + cover images.

## Verification

Run from `prototypes/`:

1. `node --check <name>/app.js && node --check <name>/games.js`
2. Selector audit — each page must contain its own hooks (home: the 4
   `data-stat` + `[data-picks]` + `[data-toggle-signin]`; search:
   `[data-search][data-genres][data-results][data-count][data-hint]`;
   backlog: `[data-sort][data-refresh][data-bblist=...][data-count-...]
   [data-empty]`) and none of the other pages' hooks.
3. `node shared/app.domtest.mjs` — must finish "ALL CHECKS PASSED" (proves
   `shared/app.js` was not broken; do not edit it).
4. Serve + curl: every page and asset returns 200, e.g. a one-liner static
   server then `curl -s -o /dev/null -w "%{http_code}"` on the 3 pages,
   `styles.css`, `games.js`, `app.js`, and the root `../index.html`.