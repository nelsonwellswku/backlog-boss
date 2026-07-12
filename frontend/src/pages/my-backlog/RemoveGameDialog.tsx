import type { BacklogGameRow } from "@bb/client";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";

type RemoveGameDialogProps = {
  open: boolean;
  game: BacklogGameRow | null;
  isUpdating: boolean;
  onClose: () => void;
  onConfirm: (game: BacklogGameRow) => void;
};

export function RemoveGameDialog({
  open,
  game,
  isUpdating,
  onClose,
  onConfirm,
}: RemoveGameDialogProps) {
  return (
    <Dialog open={open} onClose={isUpdating ? undefined : onClose}>
      <DialogTitle>Remove game from backlog?</DialogTitle>
      <DialogContent>
        <DialogContentText>
          {game
            ? `Remove ${game.title} from your backlog? It will be hidden from this page, but can be re-added later.`
            : ""}
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button disabled={isUpdating} onClick={onClose}>
          Cancel
        </Button>
        <Button
          color="error"
          disabled={isUpdating}
          variant="contained"
          onClick={() => game && onConfirm(game)}
        >
          Remove
        </Button>
      </DialogActions>
    </Dialog>
  );
}
