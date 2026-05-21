import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import PlaylistAddIcon from "@mui/icons-material/PlaylistAdd";
import ScheduleIcon from "@mui/icons-material/Schedule";
import StarIcon from "@mui/icons-material/Star";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Divider from "@mui/material/Divider";
import Link from "@mui/material/Link";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { Link as RouterLink } from "react-router";

import type { GameSearchRow } from "@bb/client";
import { GameSearchForm } from "@bb/pages/games/GameSearchForm";

type GamesViewProps = {
  addedGameIds: Set<number>;
  addingGameId: number | null;
  backlogGameIds: Set<number>;
  errorMessage: string | null;
  hasBacklog: boolean;
  hasSearched: boolean;
  isBacklogLoading: boolean;
  isError: boolean;
  isLoggedIn: boolean;
  isPending: boolean;
  onAddToBacklog: (gameId: number) => void;
  onSearch: (query: string) => Promise<GameSearchRow[]>;
  onSubmitSuccess: (results: GameSearchRow[]) => void;
  results: GameSearchRow[];
  submittedQuery: string;
};

export function GamesView({
  addedGameIds,
  addingGameId,
  backlogGameIds,
  errorMessage,
  hasBacklog,
  hasSearched,
  isBacklogLoading,
  isError,
  isLoggedIn,
  isPending,
  onAddToBacklog,
  onSearch,
  onSubmitSuccess,
  results,
  submittedQuery,
}: GamesViewProps) {
  return (
    <Box sx={{ maxWidth: 900, mx: "auto", mt: 4 }}>
      <GameSearchForm
        onSearch={onSearch}
        isPending={isPending}
        onSubmitSuccess={onSubmitSuccess}
      />

      {isError ? (
        <Alert severity="error" sx={{ mb: 3 }}>
          {errorMessage ??
            "We couldn't search for games right now. Please try again."}
        </Alert>
      ) : null}

      {isLoggedIn && !hasBacklog && !isBacklogLoading ? (
        <Alert severity="error" sx={{ mb: 3 }}>
          You don&apos;t have a backlog yet.{" "}
          <Link component={RouterLink} to="/my-backlog">
            Create your backlog
          </Link>
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
          <Stack direction="row" spacing={2} sx={{ alignItems: "center" }}>
            <CircularProgress size={32} />
            <Box>
              <Typography variant="h6" gutterBottom>
                Searching for "{submittedQuery}"
              </Typography>
              <Typography color="text.secondary">
                Pulling matching games from the local catalog and IGDB if
                needed.
              </Typography>
            </Box>
          </Stack>
        </Paper>
      ) : null}

      {hasSearched && !isPending && !isError ? (
        results.length === 0 ? (
          <Alert severity="info">No games found for "{submittedQuery}".</Alert>
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
                {results.length} game{results.length === 1 ? "" : "s"} matching
                "{submittedQuery}"
              </Typography>
            </Box>
            <List sx={{ py: 0 }}>
              {results.map((game, index) => (
                <Box key={game.gameId}>
                  <ListItem
                    sx={{ py: 2.5, px: 3 }}
                    secondaryAction={
                      isLoggedIn && hasBacklog ? (
                        backlogGameIds.has(game.gameId) ||
                        addedGameIds.has(game.gameId) ? (
                          <Chip
                            size="small"
                            icon={<CheckCircleIcon />}
                            label="In backlog"
                            color="success"
                            variant="outlined"
                          />
                        ) : (
                          <Button
                            size="small"
                            variant="outlined"
                            disabled={addingGameId === game.gameId}
                            startIcon={<PlaylistAddIcon />}
                            onClick={() => onAddToBacklog(game.gameId)}
                          >
                            {addingGameId === game.gameId
                              ? "Adding…"
                              : "Add to backlog"}
                          </Button>
                        )
                      ) : null
                    }
                  >
                    <ListItemText
                      primary={
                        <Stack
                          direction={{ xs: "column", md: "row" }}
                          spacing={1.5}
                          sx={{
                            alignItems: { xs: "flex-start", md: "center" },
                          }}
                        >
                          <Typography variant="h6">{game.title}</Typography>
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
