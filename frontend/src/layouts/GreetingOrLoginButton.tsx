import { Typography } from "@mui/material";
import { useCurrentUser } from "@bb/hooks/useCurrentUser";
import { SteamButton } from "@bb/layouts/SteamButton";

export function GreetingOrLoginButton() {
  const { isSuccess, data } = useCurrentUser(false);

  if (isSuccess && data.data) {
    return <Typography>Hello, {data.data.personaName}</Typography>;
  }

  return <SteamButton />;
}
