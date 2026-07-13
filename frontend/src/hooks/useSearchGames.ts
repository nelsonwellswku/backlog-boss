import { gameSearchGames } from "@bb/client";
import { useMutation } from "@tanstack/react-query";

type SearchGamesParams = {
  query: string;
};

export function useSearchGames() {
  return useMutation({
    mutationKey: ["search-games"],
    mutationFn: ({ query }: SearchGamesParams) =>
      gameSearchGames({
        query: { query },
        throwOnError: true,
      }),
  });
}
