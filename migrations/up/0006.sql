drop index if exists UQ_Game_IgdbGameId on Game;
drop index if exists UQ_Game_SteamGameId on Game;

drop index if exists UQ_BacklogGame_BacklogId_GameId on BacklogGame;

alter table BacklogGame
drop constraint FK_BacklogGame_GameId;

alter table BacklogGame
drop column GameId

drop table Game;

alter table BacklogGame
add IgdbGameId int not null;

alter table BacklogGame
add constraint FK_BacklogGame_IgdbGameId
foreign key (IgdbGameId) references IgdbGame(Id);
