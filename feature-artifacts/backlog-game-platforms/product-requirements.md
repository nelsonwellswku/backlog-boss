# Backlog Game Platforms — Product Requirements

## Description

Games in a user's backlog and search results currently show the title, cover art, rating, time to beat, and genres — but they don't show which platforms (Windows, Mac, Linux) a game supports. Since many Steam games support only one or two of these desktop platforms, knowing platform compatibility at a glance helps users prioritize which games they can actually play right now.

This feature adds platform icons (Windows logo, Apple logo, Tux the Linux penguin) next to each game's title in the backlog view (/my-backlog) and the game search results view (/games). Platform data is fetched from IGDB, the same source as existing game metadata, and persisted alongside each game so platform availability shows reliably without repeated external lookups.

## Acceptance Criteria

- A game that supports Windows displays the Windows logo icon after its title
- A game that supports Mac displays the Apple logo icon after its title
- A game that supports Linux displays the Tux penguin icon after its title
- A game may show any combination of the three icons (e.g. Windows-only, Windows + Mac, all three)
- Icons appear in the same position across both views: directly after the game title, before the link to the Steam store page
- Platform icons are small, unobtrusive, and use familiar brand logos (Windows, Apple, Tux)
- A game with no platform data displays no icons — no greyed-out placeholders or "unknown" fallback
- When a user creates their backlog for the first time, platform data is fetched from IGDB alongside other game data (rating, time to beat, cover, genres)
- When a user refreshes their backlog, platform data is backfilled for any games that are missing it
- When a user searches for games, platform data is fetched from IGDB and displayed in the search results
- Existing games that were already in users' backlogs before this feature ships will have their platform data populated gradually — immediately on next search or refresh, with no manual action required
- Platform data is persisted so it loads instantly on subsequent visits and does not require an IGDB call on every page load
- No new user-facing settings, toggles, or configuration are introduced
