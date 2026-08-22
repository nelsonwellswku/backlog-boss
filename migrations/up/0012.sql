create table bb.RateLimitHit (
    RateLimitHitId bigint identity not null,
    RateLimitKey nvarchar(450) not null,
    WindowStart datetimeoffset not null,
    HitCount int not null,
    constraint PK_RateLimitHit primary key (RateLimitHitId),
    constraint UQ_RateLimitHit_Key_Window unique (RateLimitKey, WindowStart)
);
