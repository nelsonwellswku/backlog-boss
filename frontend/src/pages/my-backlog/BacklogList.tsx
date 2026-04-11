import { memo, useState } from "react";
import type { BacklogGameRow } from "@bb/client";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import Divider from "@mui/material/Divider";
import IconButton from "@mui/material/IconButton";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";

type PropType = {
  activeGames: BacklogGameRow[];
  completedGames: BacklogGameRow[];
  onToggleCompleted: (game: BacklogGameRow) => void;
  onRemoveGame: (game: BacklogGameRow) => void;
  updatingBacklogGameId: number | null;
};

const BacklogListItem = memo(function BacklogListItem({
  game,
  isCompleted,
  isUpdating,
  onToggleCompleted,
  onRemoveGame,
}: {
  game: BacklogGameRow;
  isCompleted: boolean;
  isUpdating: boolean;
  onToggleCompleted: (game: BacklogGameRow) => void;
  onRemoveGame: (game: BacklogGameRow) => void;
}) {
  return (
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
      <ListItemText
        primary={game.title}
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
          primary: {
            variant: "body1",
            fontWeight: 500,
            sx: {
              textDecoration: isCompleted ? "line-through" : "none",
            },
          },
        }}
      />
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
                isCompleted ? <CheckCircleIcon /> : <CheckCircleOutlineIcon />
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
              disabled={isUpdating}
              onClick={() => onRemoveGame(game)}
            >
              <DeleteOutlineIcon />
            </IconButton>
          </span>
        </Tooltip>
      </Box>
    </ListItem>
  );
});

export function BacklogList({
  activeGames,
  completedGames,
  onToggleCompleted,
  onRemoveGame,
  updatingBacklogGameId,
}: PropType) {
  const [gamePendingRemoval, setGamePendingRemoval] =
    useState<BacklogGameRow | null>(null);

  const handleRemoveRequested = (game: BacklogGameRow) => {
    setGamePendingRemoval(game);
  };

  const handleCancelRemoveGame = () => {
    setGamePendingRemoval(null);
  };

  const handleConfirmRemoveGame = () => {
    if (!gamePendingRemoval) {
      return;
    }

    onRemoveGame(gamePendingRemoval);
    setGamePendingRemoval(null);
  };

  const renderGame = (
    game: BacklogGameRow,
    index: number,
    games: BacklogGameRow[],
  ) => (
    <Box key={game.backlogGameId}>
      <BacklogListItem
        game={game}
        isCompleted={Boolean(game.completedOn)}
        isUpdating={updatingBacklogGameId === game.backlogGameId}
        onToggleCompleted={onToggleCompleted}
        onRemoveGame={handleRemoveRequested}
      />
      {index < games.length - 1 && <Divider />}
    </Box>
  );

  const scrollToCompletedGames = () => {
    document.getElementById("completed-games")?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  const scrollToTopOfBacklog = () => {
    document.getElementById("active-backlog")?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  return (
    <Stack spacing={3}>
      <Paper
        id="active-backlog"
        elevation={2}
        sx={{ borderRadius: 2, overflow: "hidden" }}
      >
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
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 2,
              flexWrap: "wrap",
            }}
          >
            <Box>
              <Typography variant="h6">Active Backlog</Typography>
              <Typography variant="body2" color="text.secondary">
                {activeGames.length} game{activeGames.length === 1 ? "" : "s"}{" "}
                to work through
              </Typography>
            </Box>
            {completedGames.length > 0 && (
              <Button
                variant="text"
                color="success"
                endIcon={<CheckCircleIcon />}
                onClick={scrollToCompletedGames}
              >
                Jump to completed games
              </Button>
            )}
          </Box>
        </Box>
        <List sx={{ py: 0 }}>
          {activeGames.map((game, index) =>
            renderGame(game, index, activeGames),
          )}
        </List>
      </Paper>

      {completedGames.length > 0 && (
        <Paper
          id="completed-games"
          elevation={1}
          sx={{
            borderRadius: 2,
            overflow: "hidden",
            border: "1px solid",
            borderColor: "success.light",
            backgroundColor: "rgba(76, 175, 80, 0.04)",
          }}
        >
          <Box
            sx={{
              px: 3,
              py: 2,
              borderBottom: "1px solid",
              borderColor: "success.light",
              background:
                "linear-gradient(180deg, rgba(76,175,80,0.12) 0%, rgba(76,175,80,0.04) 100%)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 2,
              flexWrap: "wrap",
            }}
          >
            <Box>
              <Typography variant="h6" color="success.dark">
                Completed Games
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {completedGames.length} completed game
                {completedGames.length === 1 ? "" : "s"}
              </Typography>
            </Box>
            <Button
              variant="text"
              color="inherit"
              onClick={scrollToTopOfBacklog}
            >
              Jump to top of backlog
            </Button>
          </Box>
          <List sx={{ py: 0 }}>
            {completedGames.map((game, index) =>
              renderGame(game, index, completedGames),
            )}
          </List>
        </Paper>
      )}
      <Dialog
        open={gamePendingRemoval !== null}
        onClose={updatingBacklogGameId ? undefined : handleCancelRemoveGame}
      >
        <DialogTitle>Remove game from backlog?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            {gamePendingRemoval
              ? `Remove ${gamePendingRemoval.title} from your backlog? It will be hidden from this page, but can be re-added later.`
              : ""}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button
            disabled={updatingBacklogGameId !== null}
            onClick={handleCancelRemoveGame}
          >
            Cancel
          </Button>
          <Button
            color="error"
            disabled={updatingBacklogGameId !== null}
            variant="contained"
            onClick={handleConfirmRemoveGame}
          >
            Remove
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}
