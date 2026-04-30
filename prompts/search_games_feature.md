Add a new navigation option in the navigation banner called "Games". When it is clicked, it takes you to a new page. On this page is a search field and a search button. The user may type a game name into the field and hit the button. When the button is pressed, the front-end makes an api call to the backend to search for games. The backend will first do a fuzzy search on the database for the game. If no matches are found, the api will query the igdb api by for the game. If there are any results in the search from the igdb api, those games will be added to the database if they do not already exist. The results of the query (database search + optional igdb search) should be returned to the front-end. The front-end will then display the results in an attractively formatted list that matches the current styling of the application.

Some notes about the feature:

- anyone can see the Games navigation link and also the games page
- when searching igdb api for games, it must be constrained only to Steam games (external_game_source = 1)
- when searching igdb api, all the relevant information for a game should be fetched - identify what "relevant information" is by seeing what the application already queries for and utilizes.

Please ask questions while you build the plan if you do not understand.

Here's the full schema dump (application tables only — ignore the `bbgrate.*` tables, those are Grate migration bookkeeping):

---

## Tables

### bb.AppSession
| Column | Type | Nullable | Default |
|---|---|---|---|
| `AppSessionId` | bigint | NOT NULL | |
| `AppSessionKey` | uniqueidentifier | NOT NULL | `newid()` |
| `AppUserId` | int | NOT NULL | |
| `ExpirationDate` | datetimeoffset | NOT NULL | |

### bb.AppUser
| Column | Type | Nullable |
|---|---|---|
| `AppUserId` | int | NOT NULL |
| `SteamId` | nvarchar(17) | NOT NULL |
| `PersonaName` | nvarchar(32) | NOT NULL |
| `FirstName` | nvarchar(20) | NULL |
| `LastName` | nvarchar(20) | NULL |

### bb.Backlog
| Column | Type | Nullable |
|---|---|---|
| `BacklogId` | int | NOT NULL |
| `AppUserId` | int | NOT NULL |

### bb.BacklogGame
| Column | Type | Nullable |
|---|---|---|
| `BacklogGameId` | int | NOT NULL |
| `BacklogId` | int | NOT NULL |
| `IgdbGameId` | int | NOT NULL |
| `CompletedOn` | datetimeoffset | NULL |
| `RemovedOn` | datetimeoffset | NULL |

### bb.IgdbGame
| Column | Type | Nullable |
|---|---|---|
| `Id` | int | NOT NULL |
| `Name` | nvarchar(255) | NOT NULL |
| `TotalRating` | decimal(8,5) | NULL |

### bb.IgdbGameTimeToBeat
| Column | Type | Nullable |
|---|---|---|
| `Id` | int | NOT NULL |
| `IgdbGameId` | int | NOT NULL |
| `Normally` | int | NULL |

### bb.IgdbExternalGame
| Column | Type | Nullable |
|---|---|---|
| `Id` | int | NOT NULL |
| `Uid` | int | NOT NULL |
| `IgdbGameId` | int | NOT NULL |
| `IgdbExternalGameSourceId` | int | NOT NULL |

### bb.IgdbExternalGameSource
| Column | Type | Nullable |
|---|---|---|
| `Id` | int | NOT NULL |
| `Name` | varchar(32) | NOT NULL |

---

## Primary Keys & Unique Constraints
- **PK** `bb.AppSession.AppSessionId`
- **PK** `bb.AppUser.AppUserId`
- **UQ** `bb.AppUser.SteamId`
- **PK** `bb.Backlog.BacklogId`
- **PK** `bb.BacklogGame.BacklogGameId`
- **PK** `bb.IgdbGame.Id`
- **PK** `bb.IgdbGameTimeToBeat.Id`
- **PK** `bb.IgdbExternalGame.Id`
- **PK** `bb.IgdbExternalGameSource.Id`

---

## Foreign Keys
- `bb.AppSession.AppUserId` → `bb.AppUser.AppUserId`
- `bb.Backlog.AppUserId` → `bb.AppUser.AppUserId`
- `bb.BacklogGame.BacklogId` → `bb.Backlog.BacklogId`
- `bb.BacklogGame.IgdbGameId` → `bb.IgdbGame.Id`
- `bb.IgdbExternalGame.IgdbGameId` → `bb.IgdbGame.Id`
- `bb.IgdbExternalGame.IgdbExternalGameSourceId` → `bb.IgdbExternalGameSource.Id`
- `bb.IgdbGameTimeToBeat.IgdbGameId` → `bb.IgdbGame.Id`

---

## Non-trivial Indexes
| Table | Index | Type | Columns |
|---|---|---|---|
| `bb.AppSession` | `IX_AppSession_AppSessionKey_AppUserId_ExpirationDate` | NONCLUSTERED | `AppSessionKey, ExpirationDate` |
| `bb.AppUser` | `UQ_AppUser_SteamId` | NONCLUSTERED UNIQUE | `SteamId` |
| `bb.Backlog` | `UQ_Backlog_AppUserId` | NONCLUSTERED UNIQUE | `AppUserId` |
| `bb.BacklogGame` | `IX_BacklogGame_CompletedOn` | NONCLUSTERED | `CompletedOn` |
| `bb.BacklogGame` | `IX_BacklogGame_RemovedOn` | NONCLUSTERED | `RemovedOn` |
| `bb.BacklogGame` | `UQ_BacklogGame_BacklogId_IgdbGameId` | NONCLUSTERED UNIQUE | `BacklogId, IgdbGameId` |
| `bb.IgdbExternalGame` | `UQ_Uid_IgdbExternalGameSourceId` | NONCLUSTERED UNIQUE | `Uid, IgdbExternalGameSourceId` |
