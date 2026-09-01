import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { userGetMyBacklog } from "@bb/client";

export function useGetMyBacklogTab(status: "active" | "completed") {
  return useQuery({
    queryKey: ["myBacklog", status],
    queryFn: () => userGetMyBacklog({ query: { status } }),
    retry: false,
    placeholderData: keepPreviousData,
  });
}
