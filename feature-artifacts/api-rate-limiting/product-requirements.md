# API Rate Limiting — Product Requirements

## Description

Refreshing a backlog is an expensive operation: it reaches out to Steam for the user's owned games and to IGDB for game data, covers, genres, and platforms. A user who repeatedly clicks the "Refresh Backlog" button — or calls the underlying endpoint directly with an HTTP client — can generate a flood of these expensive requests, wasting third-party API quota and slowing things down for everyone.

This feature introduces rate limiting on the refresh-backlog operation. Each user may trigger the refresh at most once per minute; additional attempts within that minute are rejected. The limit is generous enough that no normal user will ever notice it — it exists purely to stop hammering.

The solution is built so the same protection can be applied to other operations later, with limits chosen per operation at the point of use.

## Acceptance Criteria

- A logged-in user can successfully refresh their backlog once, then must wait until the next clock minute to do so again
- If a user exceeds the allowed number of refreshes within a minute, they receive a clear "too many requests" rejection instead of triggering another refresh
- The rejection tells the client how long to wait before trying again
- Rate limiting is per user — one user's activity never blocks or counts against another user's
- Requests rejected by the rate limiter do not consume additional quota or perform any of the expensive work (no Steam or IGDB calls)
- Users who are not logged in are rejected as usual (authentication failure) without consuming any rate limit allowance
- The frontend requires no changes — users abusing the button simply see nothing happen; normal users never hit the limit
- The system remains fully functional across multiple server instances: usage counted against one instance is visible to all others
- If two attempts arrive simultaneously, exactly one is allowed and the other is rejected — the count is never silently doubled or lost
- The feature adds no new user-visible interface elements, settings, or actions
