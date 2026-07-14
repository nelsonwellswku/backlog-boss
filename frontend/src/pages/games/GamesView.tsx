import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Link from "@mui/material/Link";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { SubmitEventHandler } from "react";
import { Link as RouterLink } from "react-router";

import type { GameSearchRow } from "@bb/client";
import { SearchForm } from "@bb/pages/games/SearchForm";
import { SearchResults } from "@bb/pages/games/SearchResults";
import { SearchResultsSkeleton } from "@bb/pages/games/SearchResultsSkeleton";

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
  onQueryChange: (value: string) => void;
  onSearch: SubmitEventHandler<HTMLFormElement>;
  query: string;
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
  onQueryChange,
  onSearch,
  query,
  results,
  submittedQuery,
}: GamesViewProps) {
  return (
    <Box sx={{ mt: 4 }}>
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

          <SearchForm
            query={query}
            isPending={isPending}
            onQueryChange={onQueryChange}
            onSearch={onSearch}
          />
        </Stack>
      </Paper>

      {isError ? (
        <Alert severity="error" sx={{ mb: 3 }}>
          {errorMessage ??
            "We couldn't search for games right now. Please try again."}
        </Alert>
      ) : null}

      {isLoggedIn && !hasBacklog && !isBacklogLoading ? (
        <Alert severity="error" sx={{ mb: 3 }}>
          You don't have a backlog yet.{" "}
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
        <SearchResultsSkeleton submittedQuery={submittedQuery} />
      ) : null}

      {hasSearched && !isPending && !isError ? (
        <SearchResults
          addedGameIds={addedGameIds}
          addingGameId={addingGameId}
          backlogGameIds={backlogGameIds}
          hasBacklog={hasBacklog}
          isLoggedIn={isLoggedIn}
          results={results}
          submittedQuery={submittedQuery}
          onAddToBacklog={onAddToBacklog}
        />
      ) : null}
    </Box>
  );
}
