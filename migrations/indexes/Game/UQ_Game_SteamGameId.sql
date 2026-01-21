drop index if exists UQ_Game_SteamGameId on Game;
create unique index UQ_Game_SteamGameId on Game (SteamGameId);
