drop index if exists IX_BacklogGame_RemovedOn on bb.BacklogGame;

create nonclustered index IX_BacklogGame_RemovedOn
    on bb.BacklogGame (RemovedOn);
