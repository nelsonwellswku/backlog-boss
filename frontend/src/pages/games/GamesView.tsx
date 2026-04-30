import SearchIcon from "@mui/icons-material/Search";
import ScheduleIcon from "@mui/icons-material/Schedule";
import SportsEsportsIcon from "@mui/icons-material/SportsEsports";
import StarIcon from "@mui/icons-material/Star";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import type { FormEventHandler } from "react";

import type { GameSearchRow } from "@bb/client";

type GamesViewProps = {
  errorMessage: string | null;
  hasSearched: boolean;
  isError: boolean;
  isPending: boolean;
  onQueryChange: (value: string) => void;
  onSearch: FormEventHandler<HTMLFormElement>;
  query: string;
  results: GameSearchRow[];
  submittedQuery: string;
};

export function GamesView({
  errorMessage,
  hasSearched,
  isError,
  isPending,
  onQueryChange,
  onSearch,
  query,
  results,
  submittedQuery,
}: GamesViewProps) {
  const isSearchDisabled = query.trim().length === 0 || isPending;

  return (
    <Box sx={{ maxWidth: 900, mx: "auto", mt: 4 }}>
      <Paper
        elevation={3}
        sx={{
          p: { xs: 3, md: 4 },
          mb: 4,
          borderRadius: 3,
          background:
            "linear-gradient(135deg, rgba(102,126,234,0.15) 0%, rgba(118,75,162,0.12) 100%)",
        }}
      >
        <Stack spacing={3}>
          <Box>
            <Typography
              variant="h3"
              component="h1"
              gutterBottom
              sx={{ fontWeight: "bold" }}
            >
              Discover Games
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Search the Backlog Boss catalog and, when needed, pull fresh Steam
              game data from IGDB.
            </Typography>
          </Box>

          <Box component="form" onSubmit={onSearch}>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField
                fullWidth
                label="Game name"
                value={query}
                onChange={(event) => onQueryChange(event.target.value)}
              />
              <Button
                type="submit"
                variant="contained"
                size="large"
                disabled={isSearchDisabled}
                startIcon={<SearchIcon />}
                sx={{ minWidth: { md: 180 } }}
              >
                {isPending ? "Searching…" : "Search"}
              </Button>
            </Stack>
          </Box>
        </Stack>
      </Paper>

      {isError ? (
        <Alert severity="error" sx={{ mb: 3 }}>
          {errorMessage ?? "We couldn't search for games right now. Please try again."}
        </Alert>
      ) : null}

      {!hasSearched && !isPending ? (
        <Paper
          variant="outlined"
          sx={{ p: 3, borderRadius: 3, bgcolor: "background.paper" }}
        >
          <Typography variant="h6" gutterBottom>
            Search by title
          </Typography>
          <Typography color="text.secondary">
            Results include the game name, review score, and time-to-beat when
            available.
          </Typography>
        </Paper>
      ) : null}

      {isPending ? (
        <Paper
          variant="outlined"
          sx={{ p: 3, borderRadius: 3, bgcolor: "background.paper" }}
        >
          <Typography variant="h6" gutterBottom>
            Searching for "{submittedQuery}"
          </Typography>
          <Typography color="text.secondary">
            Pulling matching games from the local catalog and IGDB if needed.
          </Typography>
        </Paper>
      ) : null}

      {hasSearched && !isPending && !isError ? (
        results.length === 0 ? (
          <Alert severity="info">
            No games found for "{submittedQuery}".
          </Alert>
        ) : (
          <Paper elevation={2} sx={{ borderRadius: 3, overflow: "hidden" }}>
            <Box
              sx={{
                px: 3,
                py: 2,
                borderBottom: "1px solid",
                borderColor: "divider",
                background:
                  "linear-gradient(180deg, rgba(25,118,210,0.08) 0%, rgba(25,118,210,0.02) 100%)",
              }}
            >
              <Typography variant="h6">Search Results</Typography>
              <Typography variant="body2" color="text.secondary">
                {results.length} game{results.length === 1 ? "" : "s"} matching "
                {submittedQuery}"
              </Typography>
            </Box>
            <List sx={{ py: 0 }}>
              {results.map((game, index) => (
                <Box key={game.gameId}>
                  <ListItem sx={{ py: 2.5, px: 3 }}>
                    <ListItemText
                      primary={
                        <Stack
                          direction={{ xs: "column", md: "row" }}
                          spacing={1.5}
                          sx={{ alignItems: { xs: "flex-start", md: "center" } }}
                        >
                          <Typography variant="h6">{game.title}</Typography>
                          <Chip
                            size="small"
                            color="primary"
                            icon={<SportsEsportsIcon />}
                            label={`IGDB #${game.gameId}`}
                          />
                        </Stack>
                      }
                      secondary={
                        <Stack
                          direction="row"
                          spacing={1}
                          sx={{ mt: 1.5, flexWrap: "wrap", rowGap: 1 }}
                        >
                          <Chip
                            size="small"
                            icon={<StarIcon />}
                            label={
                              game.totalRating !== null
                                ? `${Math.round(game.totalRating)}/100 rating`
                                : "Rating unavailable"
                            }
                          />
                          <Chip
                            size="small"
                            icon={<ScheduleIcon />}
                            label={
                              game.timeToBeat !== null
                                ? `${Math.round(game.timeToBeat / 3600)}h to beat`
                                : "Time to beat unavailable"
                            }
                          />
                        </Stack>
                      }
                    />
                  </ListItem>
                  {index < results.length - 1 ? <Divider /> : null}
                </Box>
              ))}
            </List>
          </Paper>
        )
      ) : null}
    </Box>
  );
}
