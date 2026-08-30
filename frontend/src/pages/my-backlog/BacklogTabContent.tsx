import { useState } from "react";
import type { BacklogGameRow } from "@bb/client";
import List from "@mui/material/List";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import { BacklogListItem } from "./BacklogListItem";
import { RemoveGameDialog } from "./RemoveGameDialog";

type BacklogTabContentProps = {
  games: BacklogGameRow[];
  optimisticOverrides: Map<number, boolean>;
  onToggleCompleted: (game: BacklogGameRow) => void;
  onRemoveGame: (game: BacklogGameRow) => void;
  updatingBacklogGameId: number | null;
  emptyMessage: string;
};

export function BacklogTabContent({
  games,
  optimisticOverrides,
  onToggleCompleted,
  onRemoveGame,
  updatingBacklogGameId,
  emptyMessage,
}: BacklogTabContentProps) {
  const [gamePendingRemoval, setGamePendingRemoval] =
    useState<BacklogGameRow | null>(null);

  if (games.length === 0) {
    return (
      <Paper elevation={2} sx={{ borderRadius: 2, p: 4, textAlign: "center" }}>
        <Typography color="text.secondary">{emptyMessage}</Typography>
      </Paper>
    );
  }

  return (
    <>
      <Paper
        elevation={2}
        sx={{ borderRadius: 2, overflow: "hidden" }}
      >
        <List sx={{ py: 0 }}>
          {games.map((game, index) => (
            <BacklogListItem
              key={game.backlogGameId}
              game={game}
              isCompleted={
                optimisticOverrides.get(game.backlogGameId) ??
                Boolean(game.completedOn)
              }
              isLast={index === games.length - 1}
              isUpdating={updatingBacklogGameId === game.backlogGameId}
              onToggleCompleted={onToggleCompleted}
              onRemoveGame={() => setGamePendingRemoval(game)}
            />
          ))}
        </List>
      </Paper>
      <RemoveGameDialog
        open={gamePendingRemoval !== null}
        game={gamePendingRemoval}
        isUpdating={updatingBacklogGameId !== null}
        onClose={() => setGamePendingRemoval(null)}
        onConfirm={(game) => {
          onRemoveGame(game);
          setGamePendingRemoval(null);
        }}
      />
    </>
  );
}
