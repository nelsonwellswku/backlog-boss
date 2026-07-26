# Database Schema Reference

Schema: `bb`

## bb.AppSession

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| AppSessionId | bigint(19) | NO |  | PK |
| AppSessionKey | uniqueidentifier | NO | newid() |  |
| AppUserId | int(10) | NO |  | FK → AppUser.AppUserId |
| ExpirationDate | datetimeoffset | NO |  |  |

## bb.AppUser

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| AppUserId | int(10) | NO |  | PK |
| SteamId | nvarchar(17) | NO |  | UNIQUE |
| PersonaName | nvarchar(32) | NO |  |  |
| FirstName | nvarchar(20) | YES |  |  |
| LastName | nvarchar(20) | YES |  |  |

## bb.Backlog

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| BacklogId | int(10) | NO |  | PK |
| AppUserId | int(10) | NO |  | FK → AppUser.AppUserId |

## bb.BacklogGame

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| BacklogGameId | int(10) | NO |  | PK |
| BacklogId | int(10) | NO |  | FK → Backlog.BacklogId |
| IgdbGameId | int(10) | NO |  | FK → IgdbGame.Id |
| CompletedOn | datetimeoffset | YES |  |  |
| RemovedOn | datetimeoffset | YES |  |  |

## bb.IgdbExternalGame

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| Id | int(10) | NO |  | PK |
| Uid | int(10) | NO |  |  |
| IgdbGameId | int(10) | NO |  | FK → IgdbGame.Id |
| IgdbExternalGameSourceId | int(10) | NO |  | FK → IgdbExternalGameSource.Id |

## bb.IgdbExternalGameSource

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| Id | int(10) | NO |  | PK |
| Name | varchar(32) | NO |  |  |

## bb.IgdbGame

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| Id | int(10) | NO |  | PK |
| Name | nvarchar(255) | NO |  |  |
| TotalRating | decimal(8,5) | YES |  |  |
| CoverImageId | nvarchar(100) | YES |  |  |

## bb.IgdbGameGenre

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| IgdbGameId | int(10) | NO |  | PK, FK → IgdbGame.Id |
| IgdbGenreId | int(10) | NO |  | PK, FK → IgdbGenre.Id |

## bb.IgdbGameTimeToBeat

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| Id | int(10) | NO |  | PK |
| IgdbGameId | int(10) | NO |  | FK → IgdbGame.Id |
| Normally | int(10) | YES |  |  |

## bb.IgdbGenre

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| Id | int(10) | NO |  | PK |
| Name | varchar(100) | NO |  |  |
