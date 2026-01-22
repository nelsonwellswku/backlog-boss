import { useQuery } from "@tanstack/react-query";
import { userGetMyBacklog } from "../client";

export function useGetMyBacklog() {
  return useQuery({
    queryKey: ["myBacklog"],
    queryFn: () => userGetMyBacklog(),
  });
}
