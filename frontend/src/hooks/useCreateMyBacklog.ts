import { userCreateMyBacklog } from "@bb/client";
import { useMutation } from "@tanstack/react-query";

export function useCreateMyBacklog() {
  return useMutation({
    mutationKey: ["create-my-backlog"],
    mutationFn: () => userCreateMyBacklog(),
  });
}
