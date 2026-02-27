drop index if exists UQ_Backlog_AppUserId on bb.Backlog;
create unique index UQ_Backlog_AppUserId on bb.Backlog (AppUserId);
