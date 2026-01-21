drop index if exists UQ_Game_IgdbGameId on Game;
create unique index UQ_Game_IgdbGameId on Game (IgdbGameId);
