# Refresh Backlog Genres — Product Requirements

## Description

When a user creates or refreshes their backlog, the system imports game data from Steam and IGDB, including genre information. However, games that were imported before genre support was added — or games where IGDB simply didn't have genre data at the time — may be missing their genre tags. This leaves gaps in the user's backlog view, making it harder to browse and filter games by category.

This feature adds background genre fetching to the existing "Refresh Backlog" flow. When a user clicks the refresh button, the system will asynchronously search for any games in their backlog that are missing genre information and fetch the genres from IGDB in the background. The user doesn't need to wait for this process to complete — their refresh happens instantly, and genres appear on their next page visit.

## Acceptance Criteria

- When a user clicks "Refresh Backlog," the refresh completes immediately (no additional waiting)
- Games in the user's backlog that are missing genre information will have their genres fetched from IGDB automatically in the background
- The background genre fetch does not affect the user's experience — no loading indicators, no page refresh, no notifications
- Once genres are fetched, they persist and are shown on subsequent visits to the backlog page
- Games that already have genre information are not re-fetched
- If IGDB does not have genres for a game, the system moves on gracefully — no errors or retries
- The feature works for all users, including those with large backlogs (hundreds of games)
- The feature is transparent — no new UI elements, settings, or user actions are introduced
