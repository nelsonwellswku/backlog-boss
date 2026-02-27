drop index if exists UQ_BacklogGame_BacklogId_IgdbGameId on bb.BacklogGame
create unique index UQ_BacklogGame_BacklogId_IgdbGameId
on bb.BacklogGame (BacklogId, IgdbGameId);
