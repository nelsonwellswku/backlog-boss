create table bb.UserOwnedGame (
    UserOwnedGameId int identity(1,1) primary key,
    AppUserId int not null foreign key references bb.AppUser(AppUserId),
    IgdbGameId int not null foreign key references bb.IgdbGame(Id),
    constraint UQ_UserOwnedGame_User_Game unique (AppUserId, IgdbGameId)
);
