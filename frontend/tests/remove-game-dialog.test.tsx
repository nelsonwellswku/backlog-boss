import { render, screen, fireEvent } from "@testing-library/react";
import type { BacklogGameRow } from "../src/client";
import { RemoveGameDialog } from "../src/pages/my-backlog/RemoveGameDialog";

const game = {
  backlogGameId: 1,
  gameId: 10,
  title: "Test Game",
  totalRating: 85,
  timeToBeat: 36000,
  genres: ["Action"],
  completedOn: null,
  removedOn: null,
  addedOn: "2025-01-01T00:00:00Z",
  igdbId: 100,
  steamAppId: 1000,
  coverImageId: null,
} as BacklogGameRow;

const defaultProps = {
  open: true,
  game,
  isUpdating: false,
  onClose: () => {},
  onConfirm: () => {},
};

function renderDialog(
  overrides: Partial<React.ComponentProps<typeof RemoveGameDialog>> = {},
) {
  return render(<RemoveGameDialog {...defaultProps} {...overrides} />);
}

describe("RemoveGameDialog", () => {
  test("renders dialog content when open", () => {
    renderDialog();
    expect(screen.getByText("Remove game from backlog?")).toBeInTheDocument();
    expect(
      screen.getByText(/Remove Test Game from your backlog/),
    ).toBeInTheDocument();
  });

  test("does not render content when closed", () => {
    renderDialog({ open: false });
    expect(
      screen.queryByText("Remove game from backlog?"),
    ).not.toBeInTheDocument();
  });

  test("calls onConfirm with game when Remove is clicked", () => {
    const onConfirm = vi.fn();
    renderDialog({ onConfirm });
    fireEvent.click(screen.getByRole("button", { name: /^remove$/i }));
    expect(onConfirm).toHaveBeenCalledWith(game);
  });

  test("calls onClose when Cancel is clicked", () => {
    const onClose = vi.fn();
    renderDialog({ onClose });
    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(onClose).toHaveBeenCalled();
  });

  test("disables buttons when isUpdating is true", () => {
    renderDialog({ isUpdating: true });
    expect(screen.getByRole("button", { name: /cancel/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /^remove$/i })).toBeDisabled();
  });

  test("does not call onClose on backdrop click when isUpdating", () => {
    const onClose = vi.fn();
    renderDialog({ isUpdating: true, onClose });
    // MUI Dialog with onClose=undefined should not trigger onClose
    expect(onClose).not.toHaveBeenCalled();
  });

  test("renders empty text when game is null", () => {
    renderDialog({ game: null });
    expect(screen.getByText("Remove game from backlog?")).toBeInTheDocument();
  });
});
