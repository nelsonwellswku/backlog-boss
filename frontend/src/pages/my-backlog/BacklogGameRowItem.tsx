import { memo } from "react";
import type { BacklogGameRow } from "@bb/client";
import Box from "@mui/material/Box";
import Divider from "@mui/material/Divider";
import { BacklogListItem } from "./BacklogListItem";

export const BacklogGameRowItem = memo(function BacklogGameRowItem({
  game,
  isLast,
  isUpdating,
  onToggleCompleted,
  onRemoveGame,
}: {
  game: BacklogGameRow;
  isLast: boolean;
  isUpdating: boolean;
  onToggleCompleted: (game: BacklogGameRow) => void;
  onRemoveGame: () => void;
}) {
  return (
    <Box>
      <BacklogListItem
        game={game}
        isCompleted={Boolean(game.completedOn)}
        isUpdating={isUpdating}
        onToggleCompleted={onToggleCompleted}
        onRemoveGame={onRemoveGame}
      />
      {!isLast && <Divider />}
    </Box>
  );
});
