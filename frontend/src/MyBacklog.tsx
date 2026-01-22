import {
  Typography,
  List,
  ListItem,
  ListItemText,
  Paper,
  Box,
  Divider,
} from "@mui/material";
import { useGetMyBacklog } from "./hooks/useGetMyBacklog";

export function MyBacklog() {
  const { data, isSuccess } = useGetMyBacklog();
  const games = data?.data?.games ?? [];

  return (
    <Box sx={{ maxWidth: 800, mx: "auto", mt: 4 }}>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: "bold" }}>
        My Backlog
      </Typography>

      {!isSuccess ? (
        <Typography>Loading…</Typography>
      ) : games.length === 0 ? (
        <Typography>No games in your backlog.</Typography>
      ) : (
        <Paper elevation={2} sx={{ borderRadius: 2 }}>
          <List sx={{ py: 0 }}>
            {games.map((g, index) => (
              <Box key={g.gameId}>
                <ListItem
                  sx={{
                    py: 2,
                    px: 3,
                    "&:hover": {
                      backgroundColor: "action.hover",
                    },
                  }}
                >
                  <ListItemText
                    primary={g.title}
                    slotProps={{
                      primary: {
                        variant: "body1",
                        fontWeight: 500,
                      },
                    }}
                  />
                </ListItem>
                {index < games.length - 1 && <Divider />}
              </Box>
            ))}
          </List>
        </Paper>
      )}
    </Box>
  );
}
