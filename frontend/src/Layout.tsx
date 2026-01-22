import {
  AppBar,
  Box,
  Container,
  CssBaseline,
  Toolbar,
  Typography,
} from "@mui/material";
import { Outlet } from "react-router";
import { GreetingOrLoginButton } from "./GreetingOrLoginButton";

export function Layout() {
  return (
    <CssBaseline enableColorScheme>
      <Box
        sx={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}
      >
        <AppBar position="static">
          <Container fixed>
            <Toolbar disableGutters>
              <Typography variant="h5" sx={{ flexGrow: 1 }}>
                Backlog Boss
              </Typography>
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
            </Toolbar>
          </Container>
        </AppBar>
      </Box>
    </CssBaseline>
  );
}
