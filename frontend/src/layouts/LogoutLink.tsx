import { useCurrentUser } from "@bb/hooks/useCurrentUser";
import { useLogoutMutation } from "@bb/hooks/useLogOut";
import { Link } from "@mui/material";
import { useNavigate } from "react-router";

export function LogoutLink() {
  const { isSuccess, data: currentUserData } = useCurrentUser(false);
  const navigate = useNavigate();
  const { mutate: logout } = useLogoutMutation();

  if (isSuccess && currentUserData?.data?.appUserId) {
    return (
      <Link
        component="button"
        onClick={() => logout(undefined, { onSuccess: () => navigate("/") })}
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
      </Link>
    );
  }

  return null;
}
