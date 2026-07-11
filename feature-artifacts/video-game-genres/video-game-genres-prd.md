# Video Game Genres

## Description

Users currently see a game's title, rating, and estimated time-to-beat when browsing games or viewing their backlog. What's missing is genre — a fundamental piece of information that helps users quickly understand what kind of game they're looking at. A player might want to scan their backlog for RPGs, check whether a search result is an action game or a strategy game, or simply get a richer at-a-glance view of each title.

This feature adds genre information to every game in the system. Genres are fetched automatically from IGDB whenever a game is imported (via Steam-linked search or backlog creation/refresh) and stored in the database. They appear as labeled chips next to each game in both the search results page and the backlog list. A game may belong to multiple genres (e.g., "Action", "Adventure"); all applicable genres are shown.

## Acceptance Criteria

- When a user searches for a game, each result shows the genre(s) that game belongs to
- When a user views their backlog, each game in the list shows its genre(s)
- Each genre is displayed as a distinct, visually scannable chip alongside the game's other metadata (rating, time-to-beat)
- Genre information is automatically populated when a game is added to the system through any import path (Steam backlog creation, backlog refresh, or name search)
- Games added to the system before this feature shipped simply have no genre chips shown — no user-visible errors or blank labels
- No new user-facing settings, buttons, or actions are required; genres appear automatically
