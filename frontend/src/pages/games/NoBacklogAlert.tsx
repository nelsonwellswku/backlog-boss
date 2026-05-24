import Alert from "@mui/material/Alert";
import Link from "@mui/material/Link";
import { Link as RouterLink } from "react-router";

export function NoBacklogAlert() {
  return (
    <Alert severity="error" sx={{ mb: 3 }}>
      You don&apos;t have a backlog yet.{" "}
      <Link component={RouterLink} to="/my-backlog">
        Create your backlog
      </Link>
    </Alert>
  );
}
