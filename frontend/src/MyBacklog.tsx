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

type SortType = "score" | "time" | "blended" | null;

function createBlendedComparator(rawGames: BacklogGameRow[]) {
  // Normalize scores and times to 0-1 range
  const scores = rawGames.map(g => g.totalRating ?? 0);
  const times = rawGames.map(g => g.timeToBeat ?? Infinity).filter(t => t !== Infinity);

  const minScore = Math.min(...scores);
  const maxScore = Math.max(...scores);
  const minTime = Math.min(...times);
  const maxTime = Math.max(...times);

  const scoreRange = maxScore - minScore || 1;
  const timeRange = maxTime - minTime || 1;

  // Normalize: higher score is better, shorter time is better
  const normalizeScore = (score: number | null) =>
    score ? (score - minScore) / scoreRange : 0;
  const normalizeTime = (time: number | null) =>
    time ? (maxTime - time) / timeRange : 0;

  return (a: BacklogGameRow, b: BacklogGameRow) => {
    // weight is 3 because that gave the blended results I was looking for
    const timeWeight = 3
    const scoreA = normalizeScore(a.totalRating) + normalizeTime(a.timeToBeat) * timeWeight;
    const scoreB = normalizeScore(b.totalRating) + normalizeTime(b.timeToBeat) * timeWeight;
    return scoreB - scoreA;
  };
}

export function MyBacklog() {
  const { data, isSuccess } = useGetMyBacklog();
  const [sortType, setSortType] = useState<SortType>(null);

  const rawGames: BacklogGameRow[] = data?.data?.games ?? [];
  const blendedComparator = useMemo(() => createBlendedComparator(rawGames), [rawGames])

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
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 3 }}>
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
            onClick={() => setSortType(sortType === "blended" ? null : "blended")}
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
