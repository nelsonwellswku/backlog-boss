import { CircularProgress, Container } from "@mui/material";
import { Navigate, Outlet } from "react-router";
import { useCurrentUser } from "@bb/hooks/useCurrentUser";

export function ProtectedRoute() {
  const { data, isSuccess } = useCurrentUser(false);

  if (!isSuccess) {
    return (
      <Container
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: "50vh",
        }}
      >
        <CircularProgress />
      </Container>
    );
  }

  if (!data?.data) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
