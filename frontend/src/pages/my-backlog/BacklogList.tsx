import { useRef } from "react";
import type { BacklogGameRow } from "@bb/client";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import List from "@mui/material/List";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { BacklogListItem } from "./BacklogListItem";
import {
  RemoveGameDialog,
  type RemoveGameDialogHandle,
} from "./RemoveGameDialog";

type BacklogListProps = {
  activeGames: BacklogGameRow[];
  completedGames: BacklogGameRow[];
  onToggleCompleted: (game: BacklogGameRow) => void;
  onRemoveGame: (game: BacklogGameRow) => void;
  updatingBacklogGameId: number | null;
};

export function BacklogList({
  activeGames,
  completedGames,
  onToggleCompleted,
  onRemoveGame,
  updatingBacklogGameId,
}: BacklogListProps) {
  const dialogRef = useRef<RemoveGameDialogHandle>(null);

  const scrollToCompletedGames = () => {
    document.getElementById("completed-games")?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  const scrollToTopOfBacklog = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
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
          {activeGames.map((game, index) => (
            <BacklogListItem
              key={game.backlogGameId}
              game={game}
              isCompleted={Boolean(game.completedOn)}
              isLast={index === activeGames.length - 1}
              isUpdating={updatingBacklogGameId === game.backlogGameId}
              onToggleCompleted={onToggleCompleted}
              onRemoveGame={() => dialogRef.current?.requestRemove(game)}
            />
          ))}
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
            {completedGames.map((game, index) => (
              <BacklogListItem
                key={game.backlogGameId}
                game={game}
                isCompleted={Boolean(game.completedOn)}
                isLast={index === completedGames.length - 1}
                isUpdating={updatingBacklogGameId === game.backlogGameId}
                onToggleCompleted={onToggleCompleted}
                onRemoveGame={() => dialogRef.current?.requestRemove(game)}
              />
            ))}
          </List>
        </Paper>
      )}
      <RemoveGameDialog
        ref={dialogRef}
        isUpdating={updatingBacklogGameId !== null}
        onRemoveGame={onRemoveGame}
      />
    </Stack>
  );
}
