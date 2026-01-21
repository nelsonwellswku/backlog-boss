drop index if exists UQ_Backlog_AppUserId on Backlog;
create unique index UQ_Backlog_AppUserId on Backlog (AppUserId);
