import type { FormEvent } from "react";
import { useState } from "react";

import type { GameSearchRow } from "@bb/client";
import { useSearchGames } from "@bb/hooks/useSearchGames";
import { GamesView } from "@bb/pages/games/GamesView";

const genericSearchError =
  "We couldn't search for games right now. Please try again.";

export function Games() {
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const { data, isError, isPending, mutate } = useSearchGames();

  const results: GameSearchRow[] = data?.data?.games ?? [];
  const hasSearched = submittedQuery.length > 0;

  const handleSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedQuery = query.trim();
    if (!trimmedQuery) {
      return;
    }

    setSubmittedQuery(trimmedQuery);
    mutate({ query: trimmedQuery });
  };

  return (
    <GamesView
      errorMessage={isError ? genericSearchError : null}
      hasSearched={hasSearched}
      isError={isError}
      isPending={isPending}
      onQueryChange={setQuery}
      onSearch={handleSearch}
      query={query}
      results={results}
      submittedQuery={submittedQuery}
    />
  );
}
