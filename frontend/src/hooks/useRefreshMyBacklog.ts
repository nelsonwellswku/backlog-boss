import { userRefreshMyBacklog } from "@bb/client";
import { useMutation, useQueryClient } from "@tanstack/react-query";

export function useRefreshMyBacklog() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationKey: ["refresh-my-backlog"],
    mutationFn: () => userRefreshMyBacklog(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["myBacklog"] });
    },
  });
}
