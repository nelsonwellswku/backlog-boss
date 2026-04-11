import { useCallback, useMemo, useState } from "react";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";

import { useGetMyBacklog } from "@bb/hooks/useGetMyBacklog";
import { useCreateMyBacklog } from "@bb/hooks/useCreateMyBacklog";
import { useUpdateBacklogGame } from "@bb/hooks/useUpdateBacklogGame";
import type { BacklogGameRow } from "@bb/client";
import { createBlendedComparator } from "@bb/pages/my-backlog/blended-comparator";
import { GameSortButtonGroup } from "@bb/pages/my-backlog/GameSortButtonGroup";
import type { SortType } from "@bb/pages/my-backlog/SortType";
import { BacklogList } from "@bb/pages/my-backlog/BacklogList";
import { BacklogCreatingLoader } from "@bb/pages/my-backlog/BacklogCreatingLoader";
import { CreateBacklogPrompt } from "@bb/pages/my-backlog/CreateBacklogPrompt";

export function MyBacklog() {
  const { data, isSuccess, refetch } = useGetMyBacklog();
  const {
    mutate: createBacklog,
    isPending: isCreating,
    isError: createError,
  } = useCreateMyBacklog();
  const {
    mutate: updateBacklogGame,
    isPending: isUpdating,
    variables: updateVariables,
  } = useUpdateBacklogGame();
  const [sortType, setSortType] = useState<SortType>(null);
  const [showCreating, setShowCreating] = useState(false);
  const [completedInSessionIds, setCompletedInSessionIds] = useState<number[]>(
    [],
  );

  const serverGames = data?.data?.games;
  const rawGames: BacklogGameRow[] = useMemo(
    () => serverGames ?? [],
    [serverGames],
  );
  const blendedComparator = useMemo(
    () => createBlendedComparator(rawGames),
    [rawGames],
  );

  const games = useMemo(
    () =>
      rawGames.toSorted((a, b) => {
        if (sortType === "score") {
          return (b.totalRating ?? 0) - (a.totalRating ?? 0);
        }
        if (sortType === "time") {
          return (a.timeToBeat ?? Infinity) - (b.timeToBeat ?? Infinity);
        }
        if (sortType === "blended") {
          return blendedComparator(a, b);
        }
        return 0;
      }),
    [blendedComparator, rawGames, sortType],
  );
  const completedInSessionSet = useMemo(
    () => new Set(completedInSessionIds),
    [completedInSessionIds],
  );
  const { activeGames, completedGames } = useMemo(() => {
    const nextActiveGames = games.filter(
      (game) =>
        !game.completedOn || completedInSessionSet.has(game.backlogGameId),
    );
    const nextCompletedGames = games.filter(
      (game) =>
        game.completedOn && !completedInSessionSet.has(game.backlogGameId),
    );

    return {
      activeGames: nextActiveGames,
      completedGames: nextCompletedGames,
    };
  }, [completedInSessionSet, games]);
  const updatingBacklogGameId = isUpdating
    ? (updateVariables?.backlogGameId ?? null)
    : null;

  const is404 = data?.response.status === 404;

  const handleCreateBacklog = () => {
    setShowCreating(true);
    createBacklog(undefined, {
      onSuccess: async () => {
        await refetch();
        setShowCreating(false);
      },
      onError: () => {
        setShowCreating(false);
      },
    });
  };

  const handleToggleCompleted = useCallback(
    (game: BacklogGameRow) => {
      const isMarkingCompleted = !game.completedOn;

      updateBacklogGame(
        {
          backlogGameId: game.backlogGameId,
          completedOn: game.completedOn ? null : new Date().toISOString(),
          removedOn: null,
        },
        {
          onSuccess: () => {
            setCompletedInSessionIds((current) => {
              if (isMarkingCompleted) {
                return current.includes(game.backlogGameId)
                  ? current
                  : [...current, game.backlogGameId];
              }

              return current.filter((id) => id !== game.backlogGameId);
            });
          },
        },
      );
    },
    [updateBacklogGame],
  );

  const handleRemoveGame = useCallback(
    (game: BacklogGameRow) => {
      updateBacklogGame(
        {
          backlogGameId: game.backlogGameId,
          completedOn: game.completedOn,
          removedOn: new Date().toISOString(),
        },
        {
          onSuccess: () => {
            setCompletedInSessionIds((current) =>
              current.filter((id) => id !== game.backlogGameId),
            );
          },
        },
      );
    },
    [updateBacklogGame],
  );

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
          <BacklogList
            activeGames={activeGames}
            completedGames={completedGames}
            onToggleCompleted={handleToggleCompleted}
            onRemoveGame={handleRemoveGame}
            updatingBacklogGameId={updatingBacklogGameId}
          />
        </>
      )}
    </Box>
  );
}
