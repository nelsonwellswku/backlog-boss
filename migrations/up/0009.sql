CREATE TABLE bb.IgdbGenre (
    Id          INT           NOT NULL PRIMARY KEY,
    Name        VARCHAR(100)  NOT NULL
);

CREATE TABLE bb.IgdbGameGenre (
    IgdbGameId  INT NOT NULL REFERENCES bb.IgdbGame(Id),
    IgdbGenreId INT NOT NULL REFERENCES bb.IgdbGenre(Id),
    PRIMARY KEY (IgdbGameId, IgdbGenreId)
);
