create table AppUser (
    appUserId int identity(1, 1) not null,
    steamId nvarchar(17) not null,
    personaName  nvarchar(32) not null,
    firstName nvarchar(20) null,
    lastName nvarchar(20) null,
    constraint PK_AppUser_appUserId primary key clustered (appUserId),
    constraint UQ_AppUser_steamId unique (steamId)
)
