-- Seed the initial admin user
if not exists (select 1 from bb.AppUser where SteamId = '76561197973372728')
    insert into bb.AppUser (SteamId, PersonaName, FirstName, LastName)
    values ('76561197973372728', 'Revenant', 'Nelson', 'Wells');

insert into bb.AppUserRole (AppUserId, Role)
select u.AppUserId, 'admin'
from bb.AppUser u
where u.SteamId = '76561197973372728'
  and not exists (
      select 1
      from bb.AppUserRole r
      where r.AppUserId = u.AppUserId
        and r.Role = 'admin'
  );
