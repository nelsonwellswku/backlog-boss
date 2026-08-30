import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Button from "@mui/material/Button";
import LinearProgress from "@mui/material/LinearProgress";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import { useQueryClient } from "@tanstack/react-query";

import { useGetMyBacklog } from "@bb/hooks/useGetMyBacklog";
import { useGetMyBacklogTab } from "@bb/hooks/useGetMyBacklogTab";
import { useCreateMyBacklog } from "@bb/hooks/useCreateMyBacklog";
import { useRefreshMyBacklog } from "@bb/hooks/useRefreshMyBacklog";
import { useUpdateBacklogGame } from "@bb/hooks/useUpdateBacklogGame";
import type { BacklogGameRow } from "@bb/client";
import { createBlendedComparator } from "@bb/pages/my-backlog/blended-comparator";
import { GameSortButtonGroup } from "@bb/pages/my-backlog/GameSortButtonGroup";
import type { SortType } from "@bb/pages/my-backlog/SortType";
import { BacklogTabContent } from "@bb/pages/my-backlog/BacklogTabContent";
import { BacklogListSkeleton } from "@bb/pages/my-backlog/BacklogListSkeleton";
import { BacklogCreatingLoader } from "@bb/pages/my-backlog/BacklogCreatingLoader";
import { CreateBacklogPrompt } from "@bb/pages/my-backlog/CreateBacklogPrompt";

type TabValue = "active" | "completed";

export function MyBacklog() {
  const { data: backlogCheck, isSuccess: backlogExists, refetch } =
    useGetMyBacklog();
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
  const { mutate: refreshBacklog, isPending: isRefreshing } =
    useRefreshMyBacklog();
  const queryClient = useQueryClient();

  const [sortType, setSortType] = useState<SortType>("score");
  const [showCreating, setShowCreating] = useState(false);
  const [activeTab, setActiveTab] = useState<TabValue>("active");
  const [completedInSessionIds, setCompletedInSessionIds] = useState<number[]>(
    [],
  );

  const activeTabQuery = useGetMyBacklogTab("active");
  const completedTabQuery = useGetMyBacklogTab("completed");

  const prevTabRef = useRef(activeTab);
  useEffect(() => {
    if (prevTabRef.current !== activeTab) {
      prevTabRef.current = activeTab;
      const query = activeTab === "active" ? activeTabQuery : completedTabQuery;
      if (query.dataUpdatedAt > 0) {
        query.refetch();
      }
    }
  }, [activeTab, activeTabQuery, completedTabQuery]);

  const is404 = backlogCheck?.response.status === 404;

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

  const handleRefreshBacklog = () => {
    refreshBacklog();
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
          onSuccess: async () => {
            setCompletedInSessionIds((current) =>
              current.filter((id) => id !== game.backlogGameId),
            );
            await queryClient.invalidateQueries({ queryKey: ["myBacklog"] });
          },
        },
      );
    },
    [updateBacklogGame, queryClient],
  );

  const activeGames = useMemo(() => {
    return activeTabQuery.data?.data?.games ?? [];
  }, [activeTabQuery.data]);

  const activeGamesRaw: BacklogGameRow[] = useMemo(
    () => activeGames ?? [],
    [activeGames],
  );

  const blendedComparator = useMemo(
    () => createBlendedComparator(activeGamesRaw),
    [activeGamesRaw],
  );

  const sortedActiveGames = useMemo(
    () =>
      activeGamesRaw.toSorted((a, b) => {
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
    [blendedComparator, activeGamesRaw, sortType],
  );

  const completedGames = useMemo(() => {
    return completedTabQuery.data?.data?.games ?? [];
  }, [completedTabQuery.data]);

  const completedInSessionSet = useMemo(
    () => new Set(completedInSessionIds),
    [completedInSessionIds],
  );

  const updatingBacklogGameId = isUpdating
    ? (updateVariables?.backlogGameId ?? null)
    : null;

  const currentQuery = activeTab === "active" ? activeTabQuery : completedTabQuery;
  const isFirstLoad =
    currentQuery.isLoading || (currentQuery.isFetching && !currentQuery.isPlaceholderData);

  return (
    <Box sx={{ mt: 4 }}>
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
      ) : !backlogExists ? (
        <BacklogListSkeleton />
      ) : (
        <>
          <Typography variant="h4" sx={{ fontWeight: "bold", mb: 3 }}>
            My Backlog
          </Typography>
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              mb: 3,
            }}
          >
            <Button
              size="small"
              variant="contained"
              onClick={handleRefreshBacklog}
              disabled={isRefreshing}
            >
              {isRefreshing ? "Refreshing…" : "Refresh Backlog"}
            </Button>
          </Box>
          {isRefreshing && <LinearProgress sx={{ mt: -2, mb: 2 }} />}
          <Tabs
            value={activeTab}
            onChange={(_, value: TabValue) => setActiveTab(value)}
            sx={{ mb: 3 }}
          >
            <Tab label="Active Backlog" value="active" />
            <Tab label="Completed Games" value="completed" />
          </Tabs>
          {activeTab === "active" && (
            <Box sx={{ mb: 2 }}>
              <GameSortButtonGroup
                sortType={sortType}
                setSortType={setSortType}
              />
            </Box>
          )}
          {isFirstLoad ? (
            <BacklogListSkeleton />
          ) : (
            <BacklogTabContent
              games={activeTab === "active" ? sortedActiveGames : completedGames}
              completedInSessionSet={completedInSessionSet}
              onToggleCompleted={handleToggleCompleted}
              onRemoveGame={handleRemoveGame}
              updatingBacklogGameId={updatingBacklogGameId}
              emptyMessage={
                activeTab === "active"
                  ? "No games in your backlog yet."
                  : "No completed games yet."
              }
            />
          )}
        </>
      )}
    </Box>
  );
}
