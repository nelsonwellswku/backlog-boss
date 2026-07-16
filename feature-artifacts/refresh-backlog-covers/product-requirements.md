# Refresh Backlog Covers — Product Requirements

## Description

When a user creates or refreshes their backlog, the system imports game data from Steam and IGDB, including cover images. However, games that were imported before cover image support was added — or games where IGDB simply didn't have cover data at the time — may be missing their cover art. This leaves gaps in the user's backlog view, making it harder to visually identify and browse games.

This feature adds background cover image fetching to the existing "Refresh Backlog" flow. When a user clicks the refresh button, the system will asynchronously search for any games in their backlog that are missing a cover image and fetch the cover from IGDB in the background. The user doesn't need to wait for this process to complete — their refresh happens instantly, and covers appear on their next page visit.

## Acceptance Criteria

- When a user clicks "Refresh Backlog," the refresh completes immediately (no additional waiting)
- Games in the user's backlog that are missing a cover image will have their covers fetched from IGDB automatically in the background
- The background cover fetch does not affect the user's experience — no loading indicators, no page refresh, no notifications
- Once a cover is fetched, it persists and is shown on subsequent visits to the backlog page
- Games that already have a cover image are not re-fetched
- If IGDB does not have a cover for a game, the system moves on gracefully — no errors or retries
- The feature works for all users, including those with large backlogs (hundreds of games)
- The feature is transparent — no new UI elements, settings, or user actions are introduced
