import { useMutation } from "@tanstack/react-query";
import { authLogout } from "@bb/client";

export function useLogoutMutation() {
  return useMutation({
    mutationFn: () => authLogout(),
  });
}
