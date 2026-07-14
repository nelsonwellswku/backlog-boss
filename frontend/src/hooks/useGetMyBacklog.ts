import { useQuery } from "@tanstack/react-query";
import { userGetMyBacklog } from "@bb/client";

export function useGetMyBacklog(enabled = true) {
  return useQuery({
    queryKey: ["myBacklog"],
    queryFn: () => userGetMyBacklog(),
    retry: false,
    enabled,
  });
}
