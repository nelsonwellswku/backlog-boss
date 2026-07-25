# Database Schema Reference

Schema: `bb`

## bb.AppUser

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| AppUserId | int | NO | identity | PK |
| SteamId | varchar(17) | NO | | |
| PersonaName | varchar(32) | NO | | |
| FirstName | varchar(20) | YES | | |
| LastName | varchar(20) | YES | | |

## bb.AppSession

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| AppSessionId | bigint | NO | identity | PK |
| AppSessionKey | uniqueidentifier | NO | newsequentialid() | UNIQUE |
| ExpirationDate | datetimeoffset | NO | | |
| AppUserId | int | NO | | FK → bb.AppUser.AppUserId |

## bb.Backlog

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| BacklogId | int | NO | identity | PK |
| AppUserId | int | NO | | FK → bb.AppUser.AppUserId, UNIQUE |

## bb.BacklogGame

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| BacklogGameId | int | NO | identity | PK |
| BacklogId | int | NO | | FK → bb.Backlog.BacklogId |
| IgdbGameId | int | NO | | FK → bb.IgdbGame.Id |
| CompletedOn | datetimeoffset | YES | | |
| RemovedOn | datetimeoffset | YES | | |

Unique constraint: (BacklogId, IgdbGameId)

## bb.IgdbGame

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| Id | int | NO | | PK |
| Name | varchar(255) | NO | | |
| TotalRating | float | YES | | |
| CoverImageId | varchar(100) | YES | | |

## bb.IgdbGenre

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| Id | int | NO | | PK |
| Name | varchar(100) | NO | | |

## bb.IgdbGameGenre

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| IgdbGameId | int | NO | | PK, FK → bb.IgdbGame.Id |
| IgdbGenreId | int | NO | | PK, FK → bb.IgdbGenre.Id |

## bb.IgdbExternalGame

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| Id | int | NO | | PK |
| Uid | int | NO | | |
| IgdbGameId | int | NO | | FK → bb.IgdbGame.Id |
| IgdbExternalGameSourceId | int | NO | | FK → bb.IgdbExternalGameSource.Id |

Unique constraint: (Uid, IgdbExternalGameSourceId)

## bb.IgdbExternalGameSource

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| Id | int | NO | | PK |
| Name | varchar(32) | NO | | |

## bb.IgdbGameTimeToBeat

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| Id | int | NO | | PK |
| Normally | int | YES | | |
| IgdbGameId | int | NO | | FK → bb.IgdbGame.Id |
