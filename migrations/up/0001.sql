create table AppUser (
    AppUserId int identity(1, 1) not null,
    SteamId nvarchar(17) not null,
    PersonaName  nvarchar(32) not null,
    FirstName nvarchar(20) null,
    LastName nvarchar(20) null,
    constraint PK_AppUser_AppUserId primary key clustered (AppUserId),
    constraint UQ_AppUser_SteamId unique (SteamId)
)

create table AppSession (
    AppSessionId bigint identity(1, 1) not null,
    AppSessionKey uniqueidentifier not null default newsequentialid(),
    AppUserId int not null,
    ExpirationDate datetimeoffset(7) not null,
    constraint PK_AppSession_AppSessionId primary key clustered (AppSessionId),
    constraint FK_AppSession_AppUserId foreign key (AppUserId) references AppUser(AppUserId)
)

create nonclustered index IX_AppSession_AppSessionKey_AppUserId_ExpirationDate
    on AppSession (AppSessionKey, ExpirationDate)
    include (AppUserId);
