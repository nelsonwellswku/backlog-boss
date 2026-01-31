import { userCreateMyBacklog } from "@bb/client";
import { useQuery } from "@tanstack/react-query";

export function useCreateMyBacklog() {
  return useQuery({
    queryKey: ["create-my-backlog"],
    queryFn: () => userCreateMyBacklog(),
  });
}
