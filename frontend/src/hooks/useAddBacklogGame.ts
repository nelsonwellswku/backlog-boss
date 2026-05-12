import { backlogGameAddGameToBacklog } from "@bb/client";
import { useMutation, useQueryClient } from "@tanstack/react-query";

type AddBacklogGameParams = {
  gameId: number;
};

export function useAddBacklogGame() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationKey: ["add-backlog-game"],
    mutationFn: ({ gameId }: AddBacklogGameParams) =>
      backlogGameAddGameToBacklog({
        body: { gameId },
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["myBacklog"] });
    },
  });
}
