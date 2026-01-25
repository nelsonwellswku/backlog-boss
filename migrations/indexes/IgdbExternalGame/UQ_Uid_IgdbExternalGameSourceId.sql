drop index if exists UQ_Uid_IgdbExternalGameSourceId on IgdbExternalGame;
create unique index UQ_Uid_IgdbExternalGameSourceId on IgdbExternalGame ([Uid], IgdbExternalGameSourceId);
