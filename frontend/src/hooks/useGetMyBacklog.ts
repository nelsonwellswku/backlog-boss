import { useQuery } from "@tanstack/react-query";
import { userGetMyBacklog } from "@bb/client";

export function useGetMyBacklog() {
  return useQuery({
    queryKey: ["myBacklog"],
    queryFn: () => userGetMyBacklog(),
    retry: false,
  });
}
