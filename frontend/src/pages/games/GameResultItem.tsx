import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import PlaylistAddIcon from "@mui/icons-material/PlaylistAdd";
import ScheduleIcon from "@mui/icons-material/Schedule";
import StarIcon from "@mui/icons-material/Star";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { GameSearchRow } from "@bb/client";

type GameResultItemProps = {
  game: GameSearchRow;
  isInBacklog: boolean;
  isRecentlyAdded: boolean;
  isAdding: boolean;
  canAdd: boolean;
  onAdd: (gameId: number) => void;
};

export function GameResultItem({
  game,
  isInBacklog,
  isRecentlyAdded,
  isAdding,
  canAdd,
  onAdd,
}: GameResultItemProps) {
  const inBacklog = isInBacklog || isRecentlyAdded;

  return (
    <ListItem
      sx={{ py: 2.5, px: 3 }}
      secondaryAction={
        canAdd ? (
          inBacklog ? (
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
              disabled={isAdding}
              startIcon={<PlaylistAddIcon />}
              onClick={() => onAdd(game.gameId)}
            >
              {isAdding ? "Adding…" : "Add to backlog"}
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
            sx={{ alignItems: { xs: "flex-start", md: "center" } }}
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
  );
}
