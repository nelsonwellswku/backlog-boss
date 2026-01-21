drop index if exists UQ_BacklogGame_BacklogId_GameId on BacklogGame;
create unique index UQ_BacklogGame_BacklogId_GameId on BacklogGame (BacklogId, GameId);
