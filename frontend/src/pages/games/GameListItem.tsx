import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import PlaylistAddIcon from "@mui/icons-material/PlaylistAdd";
import ScheduleIcon from "@mui/icons-material/Schedule";
import StarIcon from "@mui/icons-material/Star";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { GameSearchRow } from "@bb/client";
import { GenreChips } from "@bb/components/GenreChips";

type GameListItemProps = {
  addingInProgress: boolean;
  game: GameSearchRow;
  hasBacklog: boolean;
  inBacklog: boolean;
  isLast: boolean;
  isLoggedIn: boolean;
  onAddToBacklog: (gameId: number) => void;
};

export function GameListItem({
  addingInProgress,
  game,
  hasBacklog,
  inBacklog,
  isLast,
  isLoggedIn,
  onAddToBacklog,
}: GameListItemProps) {
  return (
    <Box>
      <ListItem
        sx={{ py: 2.5, px: 3 }}
        secondaryAction={
          isLoggedIn && hasBacklog ? (
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
                disabled={addingInProgress}
                startIcon={<PlaylistAddIcon />}
                onClick={() => onAddToBacklog(game.gameId)}
              >
                {addingInProgress ? "Adding…" : "Add to backlog"}
              </Button>
            )
          ) : null
        }
      >
        <ListItemText
          slotProps={{ secondary: { component: "div" } }}
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
              <GenreChips genres={game.genres} />
            </Stack>
          }
        />
      </ListItem>
      {!isLast ? <Divider /> : null}
    </Box>
  );
}
