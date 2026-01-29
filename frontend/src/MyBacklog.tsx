import { useMemo, useState } from "react";
import {
  Typography,
  List,
  ListItem,
  ListItemText,
  Paper,
  Box,
  Divider,
  Button,
  ButtonGroup,
} from "@mui/material";
import { useGetMyBacklog } from "./hooks/useGetMyBacklog";
import type { BacklogGameRow } from "./client";
import { createBlendedComparator } from "./blended-comparator";

type SortType = "score" | "time" | "blended" | null;

export function MyBacklog() {
  const { data, isSuccess } = useGetMyBacklog();
  const [sortType, setSortType] = useState<SortType>(null);

  const rawGames: BacklogGameRow[] = data?.data?.games ?? [];
  const blendedComparator = useMemo(
    () => createBlendedComparator(rawGames),
    [rawGames],
  );

  const games = [...rawGames].sort((a, b) => {
    if (sortType === "score") {
      return (b.totalRating ?? 0) - (a.totalRating ?? 0);
    } else if (sortType === "time") {
      return (a.timeToBeat ?? Infinity) - (b.timeToBeat ?? Infinity);
    } else if (sortType === "blended") {
      return blendedComparator(a, b);
    }
    return 0;
  });

  return (
    <Box sx={{ maxWidth: 800, mx: "auto", mt: 4 }}>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 3,
        }}
      >
        <Typography variant="h4" sx={{ fontWeight: "bold" }}>
          My Backlog
        </Typography>
        <ButtonGroup variant="outlined" size="small">
          <Button
            onClick={() => setSortType(sortType === "score" ? null : "score")}
            variant={sortType === "score" ? "contained" : "outlined"}
          >
            ⭐ Highest Score
          </Button>
          <Button
            onClick={() => setSortType(sortType === "time" ? null : "time")}
            variant={sortType === "time" ? "contained" : "outlined"}
          >
            ⏱️ Shortest Time
          </Button>
          <Button
            onClick={() =>
              setSortType(sortType === "blended" ? null : "blended")
            }
            variant={sortType === "blended" ? "contained" : "outlined"}
          >
            🎯 Blended
          </Button>
        </ButtonGroup>
      </Box>

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
