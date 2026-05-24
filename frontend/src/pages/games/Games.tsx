import { useMemo, useState } from "react";

import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";

import type { GameSearchRow } from "@bb/client";
import { useAddBacklogGame } from "@bb/hooks/useAddBacklogGame";
import { useCurrentUser } from "@bb/hooks/useCurrentUser";
import { useGetMyBacklog } from "@bb/hooks/useGetMyBacklog";
import { useSearchGames } from "@bb/hooks/useSearchGames";
import { GameSearchForm } from "@bb/pages/games/GameSearchForm";
import { NoBacklogAlert } from "@bb/pages/games/NoBacklogAlert";
import { NoResultsAlert } from "@bb/pages/games/NoResultsAlert";
import { SearchInstructions } from "@bb/pages/games/SearchInstructions";
import { SearchLoadingState } from "@bb/pages/games/SearchLoadingState";
import { SearchResults } from "@bb/pages/games/SearchResults";

const genericSearchError =
  "We couldn't search for games right now. Please try again.";

export function Games() {
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [addedGameIds, setAddedGameIds] = useState<Set<number>>(new Set());
  const { data, isError, isPending, mutateAsync } = useSearchGames();
  const { data: userData } = useCurrentUser(false);
  const { data: backlogData, isPending: isBacklogLoading } = useGetMyBacklog();
  const {
    mutate: addBacklogGame,
    isPending: isAdding,
    variables: addVariables,
  } = useAddBacklogGame();

  const isLoggedIn = !!userData?.data;
  const hasBacklog = !!backlogData?.data;

  const backlogGameIds = useMemo(() => {
    if (!backlogData?.data?.games) return new Set<number>();
    return new Set(backlogData.data.games.map((g) => g.gameId));
  }, [backlogData]);

  const addingGameId = isAdding && addVariables ? addVariables.gameId : null;

  const results: GameSearchRow[] = data?.data?.games ?? [];
  const hasSearched = submittedQuery.length > 0;

  const handleSearch = async (query: string): Promise<GameSearchRow[]> => {
    setSubmittedQuery(query);
    const result = await mutateAsync({ query });
    return result.data?.games ?? [];
  };

  const handleAddToBacklog = (gameId: number) => {
    addBacklogGame(
      { gameId },
      {
        onSuccess: () => {
          setAddedGameIds((prev) => {
            const next = new Set(prev);
            next.add(gameId);
            return next;
          });
        },
      },
    );
  };

  return (
    <Box sx={{ maxWidth: 900, mx: "auto", mt: 4 }}>
      <GameSearchForm
        onSearch={handleSearch}
        isPending={isPending}
        onSubmitSuccess={() => {}}
      />

      {isError ? (
        <Alert severity="error" sx={{ mb: 3 }}>
          {genericSearchError}
        </Alert>
      ) : null}

      {isLoggedIn && !hasBacklog && !isBacklogLoading ? <NoBacklogAlert /> : null}

      {!hasSearched && !isPending ? <SearchInstructions /> : null}

      {isPending ? <SearchLoadingState submittedQuery={submittedQuery} /> : null}

      {hasSearched && !isPending && !isError ? (
        results.length === 0 ? (
          <NoResultsAlert submittedQuery={submittedQuery} />
        ) : (
          <SearchResults
            results={results}
            submittedQuery={submittedQuery}
            backlogGameIds={backlogGameIds}
            addedGameIds={addedGameIds}
            addingGameId={addingGameId}
            isLoggedIn={isLoggedIn}
            hasBacklog={hasBacklog}
            onAddToBacklog={handleAddToBacklog}
          />
        )
      ) : null}
    </Box>
  );
}
