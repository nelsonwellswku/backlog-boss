
import { SteamButton } from "./SteamButton";
import { AppBar, Container, CssBaseline, Toolbar, Typography } from "@mui/material";


export function App() {
  return (
    <CssBaseline enableColorScheme>
      <AppBar>
        <Container fixed>
          <Toolbar>
            <Typography variant="h5" style={{ flexGrow: 1 }}>Backlog Boss</Typography>
            <SteamButton />
          </Toolbar>
        </Container>
      </AppBar>

      {/* routing goes here */}

      <AppBar sx={{top: "auto", bottom: 0}}>
        <Container>
          <Toolbar>
            <Typography variant="h6">Copyright &copy; 2026 Nelson Wells</Typography>
          </Toolbar>
        </Container>
      </AppBar>
    </CssBaseline>
  )
}
