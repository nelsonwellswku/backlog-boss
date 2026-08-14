# Design Prototypes — Product Requirements

## Description

The current Backlog Boss interface runs on a stock Material UI theme with only minimal custom styling. It reads clearly as a template app, and the homepage is visually loud — a stacked billboard of hero gradients, three icon cards, numbered steps, and a call-to-action banner. Users get little sense of product personality or that the product was designed as a whole.

This feature produces three throwaway visual prototypes — self-contained, framework-free HTML sites — that explore how the product could look and behave. Each prototype applies a distinctly different visual direction to the same three core surfaces: the Home page, the Game Search page, and the My Backlog page. The prototypes use real game data so reviewers can judge the layouts honestly, and they include working controls so reviewers can feel how each design responds to real interactions.

The deliverable is a decision-making aid, not a product: it exists only to help choose a visual direction for the real application and is not intended to ship or to affect the live product in any way.

## Acceptance Criteria

- Three distinct prototype sites exist, each with a clearly different visual direction:
  - A dark, full-bleed site with a left-hand navigation rail and gaming-dashboard energy
  - A light, top-navigated site with an elegant, editorial character and wide centered content
  - A light, full-bleed site with a stark, high-contrast, border-heavy aesthetic
- Each site contains three pages: Home, Game Search, and My Backlog, and navigation between the pages works within each site
- Each site is shipped as plain HTML and CSS with a self-contained data file and minimal vanilla JavaScript — no frameworks, libraries, or build tooling
- All pages are viewable in a browser without a backend, API, or database
- The prototypes display real game data: recognizable game titles, real cover art, and realistic ratings and time-to-beat values
- The following interactions work within each site: searching/filtering the game list, sorting by score, time, and blended score, adding a game to the backlog, marking a game as complete (with undo), removing a game, and refreshing the backlog
- The pages render the logged-in experience by default, and the Home page offers a way to preview the logged-out (Steam sign-in) state
- The prototype copy reuses the current product messaging but is trimmed or adapted to fit each design's character
- None of the three Home pages is as visually loud as the current homepage — the hero, feature, step, and call-to-action content is presented in a more restrained way
- The sites are designed primarily for desktop but remain usable when the browser window is narrowed
- A single entry point links to all three sites so a reviewer can move between them easily
- The prototypes are clearly throwaway artifacts: they live outside the app's source tree, are excluded from version control, and have no effect on the shipped application