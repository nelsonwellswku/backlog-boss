# Steam Store Link — Product Requirements

## Description

Users researching which game to play next often want to check the Steam store page for details like price, reviews, DLC, and system requirements. Currently, there is no way to navigate from a backlog or search result to the corresponding Steam store page — users must manually search Steam.

This feature adds a small link next to each game's title that opens the game's Steam store page in a new tab. It's available on both the My Backlog page and the Games search page, so users can jump directly to Steam from any game they encounter in the app.

## Acceptance Criteria

- A Steam link icon appears next to each game's title on the My Backlog page
- A Steam link icon appears next to each game's title on the Games search results page
- The link opens `https://store.steampowered.com/app/{steam_app_id}` in a new browser tab
- Games without a known Steam App ID do not display the link icon
- The link is visually compact (icon only, no text label) with a tooltip "Open in Steam"
- Clicking the link does not interfere with other interactions on the page (e.g., adding a game to backlog)
- The feature is purely a frontend presentation concern — no new user settings, permissions, or behaviors are introduced
