import { useMemo, useState } from "react";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";

import { useGetMyBacklog } from "@bb/hooks/useGetMyBacklog";
import type { BacklogGameRow } from "@bb/client";
import { createBlendedComparator } from "@bb/pages/my-backlog/blended-comparator";
import { GameSortButtonGroup } from "@bb/pages/my-backlog/GameSortButtonGroup";
import type { SortType } from "@bb/pages/my-backlog/SortType";
import { BacklogList } from "./BacklogList";

export function MyBacklog() {
  const { data, isSuccess, isError } = useGetMyBacklog();
  const [sortType, setSortType] = useState<SortType>(null);

  const rawGames: BacklogGameRow[] = data?.data?.games ?? [];
  const blendedComparator = useMemo(
    () => createBlendedComparator(rawGames),
    [rawGames],
  );

  const games = rawGames.toSorted((a, b) => {
    if (sortType === "score") {
      return (b.totalRating ?? 0) - (a.totalRating ?? 0);
    } else if (sortType === "time") {
      return (a.timeToBeat ?? Infinity) - (b.timeToBeat ?? Infinity);
    } else if (sortType === "blended") {
      return blendedComparator(a, b);
    }
    return 0;
  });

  return (
    <Box sx={{ maxWidth: 800, mx: "auto", mt: 4 }}>
      <GameSortButtonGroup sortType={sortType} setSortType={setSortType} />

      {!isSuccess ? (
        <Typography>Loading…</Typography>
      ) : games.length === 0 ? (
        <Typography>No games in your backlog.</Typography>
      ) : (
        <BacklogList games={games} />
      )}
    </Box>
  );
}
