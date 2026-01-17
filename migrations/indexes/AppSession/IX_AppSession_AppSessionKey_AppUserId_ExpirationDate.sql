drop index if exists IX_AppSession_AppSessionKey_AppUserId_ExpirationDate on AppSession

create nonclustered index IX_AppSession_AppSessionKey_AppUserId_ExpirationDate
    on AppSession (AppSessionKey, ExpirationDate)
    include (AppUserId);
