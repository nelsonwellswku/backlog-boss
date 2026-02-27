drop index if exists IX_AppSession_AppSessionKey_AppUserId_ExpirationDate on bb.AppSession

create nonclustered index IX_AppSession_AppSessionKey_AppUserId_ExpirationDate
    on bb.AppSession (AppSessionKey, ExpirationDate)
    include (AppUserId);
