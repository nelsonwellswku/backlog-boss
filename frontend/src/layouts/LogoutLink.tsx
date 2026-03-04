import { Typography } from "@mui/material";
import { useCurrentUser } from "@bb/hooks/useCurrentUser";

export function LogoutLink() {
  const { data } = useCurrentUser();

  if (data?.data) {
    return (
      <Typography
        component="a"
        href="/logout"
        sx={{
          color: "rgba(255,255,255,0.6)",
          textDecoration: "none",
          transition: "color 0.2s",
          "&:hover": {
            color: "rgba(255,255,255,1)",
            textDecoration: "underline",
          },
        }}
      >
        Logout
      </Typography>
    );
  }

  return null;
}
