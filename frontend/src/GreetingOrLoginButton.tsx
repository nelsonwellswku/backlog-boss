import { Typography } from "@mui/material";
import { useCurrentUser } from "./hooks/useCurrentUser";
import { SteamButton } from "./SteamButton";

export function GreetingOrLoginButton() {
  const { isError, isSuccess, data } = useCurrentUser(false);

  if (isSuccess && data.data) {
    return <Typography>Hello, {data.data.personaName}</Typography>;
  }

  if (isError) {
    return <SteamButton />;
  }

  return <></>;
}
