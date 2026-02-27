drop index if exists UQ_Uid_IgdbExternalGameSourceId on bb.IgdbExternalGame;
create unique index UQ_Uid_IgdbExternalGameSourceId on bb.IgdbExternalGame ([Uid], IgdbExternalGameSourceId);
