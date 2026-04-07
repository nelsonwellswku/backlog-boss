drop index if exists IX_BacklogGame_CompletedOn on bb.BacklogGame

create nonclustered index IX_BacklogGame_CompletedOn
    on bb.BacklogGame (CompletedOn);
