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
)

create table IgdbExternalGameSource(
    Id int not null,
    [Name] varchar(32) not null,
    constraint PK_IgdbExternalGameSource_Id primary key clustered (Id)
)

create table IgdbGameTimeToBeat(
    Id int not null,
    Normally int null,
    IgdbGameId int not null
)

alter table IgdbExternalGame
add constraint FK_IgdbExternalGame_IgdbGameId foreign key (IgdbGameId) references IgdbGame(Id);

alter table IgdbExternalGame
add constraint FK_IgdbExternalGame_IgdbExternalGameSourceId foreign key (IgdbExternalGameSourceId) references IgdbExternalGameSource(Id)

alter table IgdbGameTimeToBeat
add constraint FK_IgdbGameTimeToBeat_IdgbGameId foreign key (IgdbGameId) references IgdbGame(Id)
