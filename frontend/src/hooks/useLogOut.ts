import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authLogout } from "@bb/client";

export function useLogoutMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => authLogout(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["currentUser"] });
      queryClient.removeQueries({ queryKey: ["myBacklog"] });
    },
  });
}
