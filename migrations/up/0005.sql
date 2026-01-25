create table IgdbGame(
    Id int not null,
    [Name] nvarchar(255) not null,
    TotalRating decimal(8, 5) null,
    constraint PK_IgdbGame_Id primary key clustered (Id)
);

create table IgdbExternalGame(
    Id int not null,
    [Uid] int not null,
    IgdbGameId int not null,
    IgdbExternalGameSourceId int not null,
    constraint PK_IgdbExternalGame_Id primary key clustered (Id)
);

create table IgdbExternalGameSource(
    Id int not null,
    [Name] varchar(32) not null,
    constraint PK_IgdbExternalGameSource_Id primary key clustered (Id)
);

create table IgdbGameTimeToBeat(
    Id int not null,
    IgdbGameId int not null,
    Normally int null,
    constraint PK_IgdbGameTimeToBeat_Id primary key clustered (Id)
);

alter table IgdbExternalGame
add constraint FK_IgdbExternalGame_IgdbGameId foreign key (IgdbGameId) references IgdbGame(Id);

alter table IgdbExternalGame
add constraint FK_IgdbExternalGame_IgdbExternalGameSourceId foreign key (IgdbExternalGameSourceId) references IgdbExternalGameSource(Id);

alter table IgdbGameTimeToBeat
add constraint FK_IgdbGameTimeToBeat_IdgbGameId foreign key (IgdbGameId) references IgdbGame(Id);

insert into IgdbExternalGameSource (Id, [Name]) values
(1, 'Steam'),
(3, 'GiantBomb'),
(5, 'GOG'),
(10, 'Youtube'),
(11, 'Microsoft'),
(13, 'Apple'),
(14, 'Twitch'),
(15, 'Android'),
(20, 'Amazon'),
(22, 'Amazon Luna'),
(23, 'Amazon ADG'),
(26, 'Epic Games Store'),
(28, 'Oculus'),
(29, 'Utomik'),
(30, 'Itchio'),
(31, 'Xbox Marketplace'),
(32, 'Kartridge'),
(36, 'Playstation Store US'),
(37, 'Focus Entertainment'),
(54, 'Xbox Game Pass Ultimate Cloud'),
(55, 'GameJolt'),
(121, 'IGDB');
