-- Add LastRefreshedAt to IgdbGame
ALTER TABLE bb.IgdbGame ADD LastRefreshedAt datetimeoffset null CONSTRAINT DF_IgdbGame_LastRefreshedAt DEFAULT '2000-01-01 00:00:00 +00:00';
ALTER TABLE bb.IgdbGame DROP CONSTRAINT DF_IgdbGame_LastRefreshedAt;
ALTER TABLE bb.IgdbGame ALTER COLUMN LastRefreshedAt datetimeoffset not null;

-- Create AppUserRole table
CREATE TABLE bb.AppUserRole (
    AppUserId int not null,
    Role varchar(50) not null,
    CONSTRAINT PK_AppUserRole PRIMARY KEY (AppUserId, Role),
    CONSTRAINT FK_AppUserRole_AppUser FOREIGN KEY (AppUserId) REFERENCES bb.AppUser(AppUserId)
);

-- Assign admin role to Revenant
INSERT INTO bb.AppUserRole (AppUserId, Role)
SELECT AppUserId, 'admin' FROM bb.AppUser WHERE PersonaName = 'Revenant';

-- Create IgdbRefreshLock table
CREATE TABLE bb.IgdbRefreshLock (
    LockId varchar(50) not null PRIMARY KEY,
    StartedOn datetimeoffset not null,
    LastUpdatedOn datetimeoffset not null,
    AppUserId int not null,
    CONSTRAINT FK_IgdbRefreshLock_AppUser FOREIGN KEY (AppUserId) REFERENCES bb.AppUser(AppUserId)
);
