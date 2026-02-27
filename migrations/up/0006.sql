drop index if exists UQ_Game_IgdbGameId on bb.Game;
drop index if exists UQ_Game_SteamGameId on bb.Game;

drop index if exists UQ_BacklogGame_BacklogId_GameId on bb.BacklogGame;

alter table bb.BacklogGame
drop constraint FK_BacklogGame_GameId;

alter table bb.BacklogGame
drop column GameId;

drop table bb.Game;

alter table bb.BacklogGame
add IgdbGameId int not null;

alter table bb.BacklogGame
add constraint FK_BacklogGame_IgdbGameId
foreign key (IgdbGameId) references bb.IgdbGame(Id);
