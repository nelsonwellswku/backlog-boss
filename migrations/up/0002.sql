create table Game (
    gameId int identity(1, 1) not null,
    title nvarchar(255) not null,
    steamGameId int not null,
    igdbGameId int not null
)
