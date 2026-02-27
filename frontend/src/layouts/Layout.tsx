import {
  AppBar,
  Box,
  Container,
  CssBaseline,
  Toolbar,
  Typography,
} from "@mui/material";
import { Link, Outlet } from "react-router";
import { GreetingOrLoginButton } from "@bb/layouts/GreetingOrLoginButton";
import { useCurrentUser } from "@bb/hooks/useCurrentUser";

export function Layout() {
  const { data, isSuccess } = useCurrentUser();

  return (
    <CssBaseline enableColorScheme>
      <Box
        sx={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}
      >
        <AppBar position="static">
          <Container fixed>
            <Toolbar disableGutters>
              <Typography
                variant="h5"
                component={Link}
                to="/"
                sx={{ textDecoration: "none", color: "inherit" }}
              >
                Backlog Boss
              </Typography>
              {isSuccess && data?.data ? (
                <Typography
                  component={Link}
                  to="/my-backlog"
                  marginLeft={5}
                  sx={{ textDecoration: "none", color: "inherit" }}
                >
                  My Backlog
                </Typography>
              ) : null}
              <Box flexGrow={1} />
              <GreetingOrLoginButton />
            </Toolbar>
          </Container>
        </AppBar>

        <Container fixed sx={{ flex: 1, py: 2 }}>
          <Outlet />
        </Container>

        <AppBar position="static" component="footer">
          <Container>
            <Toolbar disableGutters>
              <Typography variant="h6">
                Copyright &copy; 2026 Nelson Wells
              </Typography>
              <Box flexGrow={1} />
              <Typography
                component="a"
                href="https://github.com/nelsonwellswku/backlog-boss"
                sx={{ textDecoration: "none", color: "inherit", mr: 3 }}
              >
                Source
              </Typography>
              <Typography
                component="a"
                href="/api/docs"
                sx={{ textDecoration: "none", color: "inherit" }}
              >
                API Docs
              </Typography>
            </Toolbar>
          </Container>
        </AppBar>
      </Box>
    </CssBaseline>
  );
}
