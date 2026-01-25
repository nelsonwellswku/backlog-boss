drop index if exists UQ_BacklogGame_BacklogId_IgdbGameId on BacklogGame
create unique index UQ_BacklogGame_BacklogId_IgdbGameId
on BacklogGame (BacklogId, IgdbGameId);
