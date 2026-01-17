
import { SteamButton } from "./SteamButton";
import { AppBar, Container, CssBaseline, Toolbar, Typography } from "@mui/material";
import {readinessApiHealthReadinessGet} from "./client"
import { useEffect, useState } from "react";


export function App() {

  const [message, setMessage] = useState<string | null>(null)

  useEffect(()=>{
    readinessApiHealthReadinessGet()
      .then(() => setMessage("Ready :)"))
      .catch(() => setMessage("Something's wrong..."))
  })

  return (
    <CssBaseline enableColorScheme>
      <AppBar position="static">
        <Container fixed>
          <Toolbar disableGutters>
            <Typography variant="h5" sx={{ flexGrow: 1 }}>Backlog Boss</Typography>
            <SteamButton />
          </Toolbar>
        </Container>
      </AppBar>

      {/* routing goes here */}

      <AppBar sx={{top: "auto", bottom: 0}}>
        <Container>
          <Toolbar disableGutters>
            <Typography variant="h6" sx={{ flexGrow: 1 }}>Copyright &copy; 2026 Nelson Wells</Typography>
            <Typography variant="body1">{message}</Typography>
          </Toolbar>
        </Container>
      </AppBar>
    </CssBaseline>
  )
}
