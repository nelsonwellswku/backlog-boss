import { useMemo, useState } from "react";

import type { GameSearchRow } from "@bb/client";
import { useAddBacklogGame } from "@bb/hooks/useAddBacklogGame";
import { useCurrentUser } from "@bb/hooks/useCurrentUser";
import { useGetMyBacklog } from "@bb/hooks/useGetMyBacklog";
import { useSearchGames } from "@bb/hooks/useSearchGames";
import { GamesView } from "@bb/pages/games/GamesView";

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
    <GamesView
      addedGameIds={addedGameIds}
      addingGameId={addingGameId}
      backlogGameIds={backlogGameIds}
      errorMessage={isError ? genericSearchError : null}
      hasBacklog={hasBacklog}
      hasSearched={hasSearched}
      isBacklogLoading={isBacklogLoading}
      isError={isError}
      isLoggedIn={isLoggedIn}
      isPending={isPending}
      onAddToBacklog={handleAddToBacklog}
      onSearch={handleSearch}
      onSubmitSuccess={() => {}}
      results={results}
      submittedQuery={submittedQuery}
    />
  );
}
