import { forwardRef, useImperativeHandle, useState } from "react";
import type { BacklogGameRow } from "@bb/client";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";

export type RemoveGameDialogHandle = {
  requestRemove: (game: BacklogGameRow) => void;
};

type RemoveGameDialogProps = {
  isUpdating: boolean;
  onRemoveGame: (game: BacklogGameRow) => void;
};

export const RemoveGameDialog = forwardRef<RemoveGameDialogHandle, RemoveGameDialogProps>(
  function RemoveGameDialog({ isUpdating, onRemoveGame }, ref) {
    const [gamePendingRemoval, setGamePendingRemoval] =
      useState<BacklogGameRow | null>(null);

    useImperativeHandle(ref, () => ({
      requestRemove: (game: BacklogGameRow) => {
        setGamePendingRemoval(game);
      },
    }));

    const handleCancel = () => {
      setGamePendingRemoval(null);
    };

    const handleConfirm = () => {
      if (!gamePendingRemoval) {
        return;
      }
      onRemoveGame(gamePendingRemoval);
      setGamePendingRemoval(null);
    };

    return (
      <Dialog
        open={gamePendingRemoval !== null}
        onClose={isUpdating ? undefined : handleCancel}
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
          <Button disabled={isUpdating} onClick={handleCancel}>
            Cancel
          </Button>
          <Button
            color="error"
            disabled={isUpdating}
            variant="contained"
            onClick={handleConfirm}
          >
            Remove
          </Button>
        </DialogActions>
      </Dialog>
    );
  },
);
