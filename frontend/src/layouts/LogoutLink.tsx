import { useCurrentUser } from "@bb/hooks/useCurrentUser";
import { useLogoutMutation } from "@bb/hooks/useLogOut";
import { Typography } from "@mui/material";
import { Navigate } from "react-router";

export function LogoutLink() {
  const {
    isError,
    data: currentUserData,
    refetch: refetchCurrentUser,
  } = useCurrentUser(false);
  const { mutate: logout } = useLogoutMutation();

  if (isError) {
    return <Navigate to="/" replace />;
  }

  if (currentUserData?.data?.appUserId) {
    return (
      <Typography
        onClick={() =>
          logout(undefined, { onSuccess: () => refetchCurrentUser() })
        }
        sx={{
          color: "rgba(255,255,255,0.6)",
          textDecoration: "none",
          transition: "color 0.2s",
          "&:hover": {
            color: "rgba(255,255,255,1)",
            textDecoration: "underline",
            cursor: "pointer",
          },
        }}
      >
        Logout
      </Typography>
    );
  }

  return null;
}
