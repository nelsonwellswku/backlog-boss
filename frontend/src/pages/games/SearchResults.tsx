import Box from "@mui/material/Box";
import Divider from "@mui/material/Divider";
import List from "@mui/material/List";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";

import type { GameSearchRow } from "@bb/client";
import { GameResultItem } from "@bb/pages/games/GameResultItem";

type SearchResultsProps = {
  results: GameSearchRow[];
  submittedQuery: string;
  backlogGameIds: Set<number>;
  addedGameIds: Set<number>;
  addingGameId: number | null;
  isLoggedIn: boolean;
  hasBacklog: boolean;
  onAddToBacklog: (gameId: number) => void;
};

export function SearchResults({
  results,
  submittedQuery,
  backlogGameIds,
  addedGameIds,
  addingGameId,
  isLoggedIn,
  hasBacklog,
  onAddToBacklog,
}: SearchResultsProps) {
  const canAdd = isLoggedIn && hasBacklog;

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
          <Box key={game.gameId}>
            <GameResultItem
              game={game}
              isInBacklog={backlogGameIds.has(game.gameId)}
              isRecentlyAdded={addedGameIds.has(game.gameId)}
              isAdding={addingGameId === game.gameId}
              canAdd={canAdd}
              onAdd={onAddToBacklog}
            />
            {index < results.length - 1 ? <Divider /> : null}
          </Box>
        ))}
      </List>
    </Paper>
  );
}
