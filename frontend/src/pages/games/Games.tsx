import type { SubmitEvent } from "react";
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
  const [searchQuery, setSearchQuery] = useState("");
  const [submittedSearchQuery, setSubmittedSearchQuery] = useState("");
  const [addedGameIds, setAddedGameIds] = useState<Set<number>>(new Set());
  const {
    data: searchGamesData,
    isError: searchIsError,
    isPending: searchIsPending,
    mutate: searchGames,
  } = useSearchGames();
  const { isSuccess, data: userData } = useCurrentUser(false);
  const isLoggedIn = isSuccess && !!userData?.data;
  const { data: backlogData, isPending: isBacklogLoading } =
    useGetMyBacklog(isLoggedIn);
  const {
    mutate: addBacklogGame,
    isPending: isAdding,
    variables: addVariables,
  } = useAddBacklogGame();

  const hasBacklog = !!backlogData?.data;

  const backlogGameIds = useMemo(() => {
    if (!backlogData?.data?.games) return new Set<number>();
    return new Set(backlogData.data.games.map((g) => g.gameId));
  }, [backlogData]);

  const addingGameId = isAdding && addVariables ? addVariables.gameId : null;

  const results: GameSearchRow[] = searchGamesData?.data?.games ?? [];
  const hasSearched = submittedSearchQuery.length > 0;

  const handleSearch = (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedQuery = searchQuery.trim();
    if (!trimmedQuery) {
      return;
    }

    setSubmittedSearchQuery(trimmedQuery);
    searchGames({ query: trimmedQuery });
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
      errorMessage={searchIsError ? genericSearchError : null}
      hasBacklog={hasBacklog}
      hasSearched={hasSearched}
      isBacklogLoading={isBacklogLoading}
      isError={searchIsError}
      isLoggedIn={isLoggedIn}
      isPending={searchIsPending}
      onAddToBacklog={handleAddToBacklog}
      onQueryChange={setSearchQuery}
      onSearch={handleSearch}
      query={searchQuery}
      results={results}
      submittedQuery={submittedSearchQuery}
    />
  );
}
