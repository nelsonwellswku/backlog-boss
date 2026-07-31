create table bb.IgdbPlatform (
    Id int not null,
    Name varchar(32) not null,
    constraint PK_IgdbPlatform primary key (Id)
);

insert into bb.IgdbPlatform (Id, Name) values
    (6, 'Windows'),
    (14, 'Mac'),
    (3, 'Linux');

create table bb.IgdbGamePlatform (
    IgdbGameId int not null,
    IgdbPlatformId int not null,
    constraint PK_IgdbGamePlatform primary key (IgdbGameId, IgdbPlatformId),
    constraint FK_IgdbGamePlatform_IgdbGame foreign key (IgdbGameId) references bb.IgdbGame(Id),
    constraint FK_IgdbGamePlatform_IgdbPlatform foreign key (IgdbPlatformId) references bb.IgdbPlatform(Id)
);
