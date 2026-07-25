# Synchronous Backlog Refresh — Product Requirements

## Description

When a user refreshes their backlog, they expect the result to reflect the current state of their Steam library and game data. Currently, the refresh flow works in two stages: the user's Steam games are imported into their backlog immediately, but cover images and genre information are fetched in the background afterwards. This means the user sees an incomplete view — games may appear without their cover art or genre tags — until the background tasks finish, which could take several seconds.

This feature makes the entire refresh process synchronous. When a user clicks the refresh button, the system fetches all data — new Steam games, cover images, and genre information — before returning a response. The frontend then automatically refetches the backlog, presenting a complete, current view in a single step. No more waiting for covers to populate on a subsequent visit.

## Acceptance Criteria

- When a user clicks "Refresh Backlog," all game data (new Steam imports, cover images, genres) is fully populated before the screen updates
- The backlog page shows the complete, current view after refresh with no missing cover images or genre tags
- Games that already have a cover image or genre data are not re-fetched from IGDB
- If IGDB is unreachable during a refresh, the entire refresh fails with an appropriate error so the user knows to retry
- The refresh button shows a loading state while the request is in flight and resolves to the updated backlog on completion
- The behavior applies to all games in the backlog, not just newly imported ones — previously missing covers and genres are fetched as part of any refresh
- No new UI elements, settings, or user actions are introduced beyond the existing refresh flow
