-- Add LastRefreshedAt to IgdbGame (with values backfills existing rows in the same statement)
alter table bb.IgdbGame add LastRefreshedAt datetimeoffset null constraint DF_IgdbGame_LastRefreshedAt default '2000-01-01 00:00:00 +00:00' with values;
alter table bb.IgdbGame drop constraint DF_IgdbGame_LastRefreshedAt;
alter table bb.IgdbGame alter column LastRefreshedAt datetimeoffset not null;

-- Create AppUserRole table
create table bb.AppUserRole (
    AppUserId int not null,
    Role varchar(50) not null,
    constraint PK_AppUserRole primary key (AppUserId, Role),
    constraint FK_AppUserRole_AppUser foreign key (AppUserId) references bb.AppUser(AppUserId)
);

-- Assign admin role to Revenant
insert into bb.AppUserRole (AppUserId, Role)
select AppUserId, 'admin' from bb.AppUser where PersonaName = 'Revenant';

-- Create IgdbRefreshLock table
create table bb.IgdbRefreshLock (
    LockId varchar(50) not null primary key,
    StartedOn datetimeoffset not null,
    LastUpdatedOn datetimeoffset not null,
    AppUserId int not null,
    constraint FK_IgdbRefreshLock_AppUser foreign key (AppUserId) references bb.AppUser(AppUserId)
);
