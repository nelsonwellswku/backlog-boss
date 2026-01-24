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
import type { BacklogGameRow } from "./client";

export function MyBacklog() {
  const { data, isSuccess } = useGetMyBacklog();
  const games: BacklogGameRow[] = data?.data?.games ?? [];

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
                    secondary={
                      <Box sx={{ display: "flex", gap: 2, mt: 0.5 }}>
                        {g.timeToBeat && (
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{
                              display: "flex",
                              alignItems: "center",
                              gap: 0.5,
                            }}
                          >
                            ⏱️ {Math.round(g.timeToBeat / 3600)}h
                          </Typography>
                        )}
                        {g.totalRating && (
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{
                              display: "flex",
                              alignItems: "center",
                              gap: 0.5,
                            }}
                          >
                            ⭐ {Math.round(g.totalRating)}/100
                          </Typography>
                        )}
                      </Box>
                    }
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
