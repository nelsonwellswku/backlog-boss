import { memo } from "react";
import type { BacklogGameRow } from "@bb/client";
import { GenreChips } from "@bb/components/GenreChips";
import { PlatformIcons } from "@bb/components/PlatformIcons";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import CheckCircleOutlinedIcon from "@mui/icons-material/CheckCircleOutlined";
import DeleteOutlinedIcon from "@mui/icons-material/DeleteOutlined";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import IconButton from "@mui/material/IconButton";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import { CoverImage } from "@bb/components/CoverImage";

export const BacklogListItem = memo(function BacklogListItem({
  game,
  isCompleted,
  isLast,
  isUpdating,
  onToggleCompleted,
  onRemoveGame,
}: {
  game: BacklogGameRow;
  isCompleted: boolean;
  isLast: boolean;
  isUpdating: boolean;
  onToggleCompleted: (game: BacklogGameRow) => void;
  onRemoveGame: (game: BacklogGameRow) => void;
}) {
  return (
    <>
      <ListItem
        sx={{
          py: 2,
          px: 2,
          opacity: isCompleted ? 0.7 : 1,
          "&:hover": {
            backgroundColor: "action.hover",
          },
        }}
      >
        <Box sx={{ display: "flex", gap: 2, flex: 1, minWidth: 0 }}>
          <CoverImage imageId={game.coverImageId} title={game.title} />

          <ListItemText
            primary={
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                <Typography
                  variant="body1"
                  sx={{
                    fontWeight: 500,
                    textDecoration: isCompleted ? "line-through" : "none",
                  }}
                >
                  {game.title}
                </Typography>
                <PlatformIcons platformIds={game.platformIds} />
                {game.steamAppId && (
                  <Tooltip title="Open in Steam">
                    <IconButton
                      size="small"
                      component="a"
                      href={`https://store.steampowered.com/app/${game.steamAppId}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      aria-label="Open in Steam"
                      sx={{ p: 0.5 }}
                    >
                      <OpenInNewIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                )}
              </Box>
            }
            secondary={
              <Box
                component="span"
                sx={{ display: "flex", flexWrap: "wrap", gap: 1, mt: 0.75 }}
              >
                {game.timeToBeat !== null && (
                  <Typography
                    component="span"
                    variant="body2"
                    color="text.secondary"
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 0.5,
                      textDecoration: isCompleted ? "line-through" : "none",
                    }}
                  >
                    ⏱️ {Math.round(game.timeToBeat / 3600)}h
                  </Typography>
                )}
                {game.totalRating !== null && (
                  <Typography
                    component="span"
                    variant="body2"
                    color="text.secondary"
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 0.5,
                      textDecoration: isCompleted ? "line-through" : "none",
                    }}
                  >
                    ⭐ {Math.round(game.totalRating)}/100
                  </Typography>
                )}
                <GenreChips genres={game.genres} />
                {game.releaseYear != null && (
                  <Typography
                    component="span"
                    variant="body2"
                    color="text.secondary"
                    sx={{
                      textDecoration: isCompleted ? "line-through" : "none",
                    }}
                  >
                    Release Date - {game.releaseYear}
                  </Typography>
                )}
                {isCompleted && (
                  <Chip
                    icon={<CheckCircleIcon />}
                    label="Completed"
                    size="small"
                    color="success"
                    variant="outlined"
                  />
                )}
              </Box>
            }
            slotProps={{
              secondary: {
                component: "div",
              },
            }}
          />
        </Box>

        <Box sx={{ display: "flex", alignItems: "center", gap: 1, ml: 2 }}>
          <Tooltip
            title={
              isCompleted
                ? "Mark this game as active again"
                : "Mark this game as completed"
            }
          >
            <span>
              <Button
                size="small"
                variant={isCompleted ? "contained" : "outlined"}
                color={isCompleted ? "success" : "inherit"}
                disabled={isUpdating}
                startIcon={
                  isCompleted ? (
                    <CheckCircleIcon />
                  ) : (
                    <CheckCircleOutlinedIcon />
                  )
                }
                onClick={() => onToggleCompleted(game)}
              >
                {isCompleted ? "Completed" : "Mark complete"}
              </Button>
            </span>
          </Tooltip>
          <Tooltip title="Remove from backlog">
            <span>
              <IconButton
                color="error"
                aria-label="Remove from backlog"
                disabled={isUpdating}
                onClick={() => onRemoveGame(game)}
              >
                <DeleteOutlinedIcon />
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      </ListItem>
      {!isLast && <Divider />}
    </>
  );
});
