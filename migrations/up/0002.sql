create table Game (
    GameId int identity(1, 1) not null,
    Title nvarchar(255) not null,
    SteamGameId int not null,
    IgdbGameId int not null,
    constraint PK_Game_GameId primary key clustered (GameId),
)
