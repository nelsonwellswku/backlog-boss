import { useQuery } from "@tanstack/react-query";
import { userGetMe } from "../client";

export function useCurrentUser(retry: boolean | number = 3) {
    return useQuery({
        queryKey: ["currentUser"],
        queryFn: () => userGetMe({throwOnError: true}),
        retry: retry
    })
}
