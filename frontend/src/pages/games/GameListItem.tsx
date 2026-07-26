import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import PlaylistAddIcon from "@mui/icons-material/PlaylistAdd";
import ScheduleIcon from "@mui/icons-material/Schedule";
import StarIcon from "@mui/icons-material/Star";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import IconButton from "@mui/material/IconButton";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Stack from "@mui/material/Stack";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";

import type { GameSearchRow } from "@bb/client";
import { CoverImage } from "@bb/components/CoverImage";
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
      <ListItem sx={{ py: 2, px: 2 }}>
        <Box sx={{ display: "flex", gap: 2, flex: 1, minWidth: 0 }}>
          <CoverImage imageId={game.coverImageId} title={game.title} />

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
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                  <Typography variant="h6">{game.title}</Typography>
                  {game.steamAppId && (
                    <Tooltip title="Open in Steam">
                      <IconButton
                        size="small"
                        component="a"
                        href={`https://store.steampowered.com/app/${game.steamAppId}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        sx={{ p: 0.5 }}
                      >
                        <OpenInNewIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                </Box>
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
        </Box>

        {isLoggedIn && hasBacklog ? (
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, ml: 2 }}>
            {inBacklog ? (
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
                {addingInProgress ? "Adding..." : "Add to backlog"}
              </Button>
            )}
          </Box>
        ) : null}
      </ListItem>
      {!isLast ? <Divider /> : null}
    </Box>
  );
}
