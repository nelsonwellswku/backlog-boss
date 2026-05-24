import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import List from "@mui/material/List";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";

import type { GameSearchRow } from "@bb/client";
import { GameListItem } from "@bb/pages/games/GameListItem";

type SearchResultsProps = {
  addedGameIds: Set<number>;
  addingGameId: number | null;
  backlogGameIds: Set<number>;
  hasBacklog: boolean;
  isLoggedIn: boolean;
  onAddToBacklog: (gameId: number) => void;
  results: GameSearchRow[];
  submittedQuery: string;
};

export function SearchResults({
  addedGameIds,
  addingGameId,
  backlogGameIds,
  hasBacklog,
  isLoggedIn,
  onAddToBacklog,
  results,
  submittedQuery,
}: SearchResultsProps) {
  if (results.length === 0) {
    return (
      <Alert severity="info">No games found for "{submittedQuery}".</Alert>
    );
  }

  return (
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
          <GameListItem
            key={game.gameId}
            addingInProgress={addingGameId === game.gameId}
            game={game}
            hasBacklog={hasBacklog}
            inBacklog={
              backlogGameIds.has(game.gameId) || addedGameIds.has(game.gameId)
            }
            isLast={index === results.length - 1}
            isLoggedIn={isLoggedIn}
            onAddToBacklog={onAddToBacklog}
          />
        ))}
      </List>
    </Paper>
  );
}
