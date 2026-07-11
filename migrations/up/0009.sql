create table bb.IgdbGenre (
    Id          int           not null primary key,
    Name        varchar(100)  not null
);

create table bb.IgdbGameGenre (
    IgdbGameId  int not null references bb.IgdbGame(Id),
    IgdbGenreId int not null references bb.IgdbGenre(Id),
    primary key (IgdbGameId, IgdbGenreId)
);
