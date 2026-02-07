import { useMemo, useState, useEffect } from "react";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";

import { useGetMyBacklog } from "@bb/hooks/useGetMyBacklog";
import { useCreateMyBacklog } from "@bb/hooks/useCreateMyBacklog";
import type { BacklogGameRow } from "@bb/client";
import { createBlendedComparator } from "@bb/pages/my-backlog/blended-comparator";
import { GameSortButtonGroup } from "@bb/pages/my-backlog/GameSortButtonGroup";
import type { SortType } from "@bb/pages/my-backlog/SortType";
import { BacklogList } from "./BacklogList";
import { BacklogCreatingLoader } from "./BacklogCreatingLoader";
import { CreateBacklogPrompt } from "./CreateBacklogPrompt";

export function MyBacklog() {
  const { data, isSuccess, refetch } = useGetMyBacklog();
  const {
    mutate: createBacklog,
    isPending: isCreating,
    isSuccess: createSuccess,
    isError: createError,
  } = useCreateMyBacklog();
  const [sortType, setSortType] = useState<SortType>(null);
  const [showCreating, setShowCreating] = useState(false);

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

  const is404 = data?.response.status === 404;

  // Refetch when creation is successful
  useEffect(() => {
    if (createSuccess) {
      setShowCreating(false);
      refetch();
    }
  }, [createSuccess, refetch]);

  const handleCreateBacklog = () => {
    setShowCreating(true);
    createBacklog();
  };

  return (
    <Box sx={{ maxWidth: 800, mx: "auto", mt: 4 }}>
      {showCreating || isCreating ? (
        <BacklogCreatingLoader />
      ) : createError ? (
        <>
          <Typography color="error" sx={{ mb: 2 }}>
            Failed to create backlog. Please try again.
          </Typography>
          <CreateBacklogPrompt onCreateBacklog={handleCreateBacklog} />
        </>
      ) : is404 ? (
        <CreateBacklogPrompt onCreateBacklog={handleCreateBacklog} />
      ) : !isSuccess ? (
        <Typography>Loading…</Typography>
      ) : games.length === 0 ? (
        <Typography>No games in your backlog.</Typography>
      ) : (
        <>
          <GameSortButtonGroup sortType={sortType} setSortType={setSortType} />
          <BacklogList games={games} />
        </>
      )}
    </Box>
  );
}
