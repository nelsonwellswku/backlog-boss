import { AppBar, Container, CssBaseline, Toolbar, Typography } from "@mui/material";
import { Outlet } from "react-router";
import { GreetingOrLoginButton } from "./GreetingOrLoginButton";

export function Layout() {
    return (
    <CssBaseline enableColorScheme>
      <AppBar position="static">
        <Container fixed>
          <Toolbar disableGutters>
            <Typography variant="h5" sx={{ flexGrow: 1 }}>Backlog Boss</Typography>
            <GreetingOrLoginButton/>
          </Toolbar>
        </Container>
      </AppBar>

      <Container fixed>
        <Outlet/>
      </Container>


      <AppBar position="static" sx={{top: "auto", bottom: 0}}>
        <Container>
          <Toolbar disableGutters>
            <Typography variant="h6">Copyright &copy; 2026 Nelson Wells</Typography>
          </Toolbar>
        </Container>
      </AppBar>
    </CssBaseline>)
}
