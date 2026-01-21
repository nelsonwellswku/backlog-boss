create table Backlog (
    BacklogId int identity(1, 1) not null,
    AppUserId int not null,
    constraint PK_Backlog_BacklogId primary key clustered (BacklogId),
    constraint FK_Backlog_AppUserId foreign key (AppUserId) references AppUser(AppUserId)
);

create table BacklogGame (
    BacklogGameId int identity(1, 1) not null,
    BacklogId int not null,
    GameId int not null,
    constraint PK_BacklogGameId primary key clustered (BacklogGameId),
    constraint FK_BacklogGame_BacklogId foreign key (BacklogId) references Backlog(BacklogId),
    constraint FK_BacklogGame_GameId foreign key (GameId) references Game(GameId)
)
