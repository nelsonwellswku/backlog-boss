import { backlogGameUpdateGame } from "@bb/client";
import { useMutation, useQueryClient } from "@tanstack/react-query";

type UpdateBacklogGameParams = {
  backlogGameId: number;
  completedOn: string | null;
  removedOn: string | null;
};

export function useUpdateBacklogGame() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationKey: ["update-backlog-game"],
    mutationFn: ({ backlogGameId, completedOn, removedOn }: UpdateBacklogGameParams) =>
      backlogGameUpdateGame({
        path: { backlog_game_id: backlogGameId },
        body: { completedOn, removedOn },
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["myBacklog"] });
    },
  });
}
