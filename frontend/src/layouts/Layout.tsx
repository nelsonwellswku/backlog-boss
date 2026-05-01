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
import { LogoutLink } from "@bb/layouts/LogoutLink";

export function Layout() {
  const { data, isSuccess } = useCurrentUser(false);

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
              <Typography
                component={Link}
                to="/games"
                sx={{ ml: 5, textDecoration: "none", color: "inherit" }}
              >
                Games
              </Typography>
              {isSuccess && data?.data ? (
                <Typography
                  component={Link}
                  to="/my-backlog"
                  sx={{ ml: 3, textDecoration: "none", color: "inherit" }}
                >
                  My Backlog
                </Typography>
              ) : null}
              <Box sx={{ flexGrow: 1 }} />
              <GreetingOrLoginButton />
              {isSuccess && data?.data?.appUserId ? (
                <Typography sx={{ mx: 1, opacity: 0.4 }}>•</Typography>
              ) : null}
              <LogoutLink />
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
              <Box sx={{ flexGrow: 1 }} />
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
