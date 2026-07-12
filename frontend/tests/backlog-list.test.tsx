import { render, screen, fireEvent } from "@testing-library/react";

import type { BacklogGameRow } from "../src/client";
import { BacklogList } from "../src/pages/my-backlog/BacklogList";

const noop = () => {};

const activeGame = {
  backlogGameId: 1,
  gameId: 10,
  title: "Active Game",
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

const completedGame: BacklogGameRow = {
  ...activeGame,
  backlogGameId: 2,
  gameId: 20,
  title: "Completed Game",
  completedOn: "2025-06-01T00:00:00Z",
};

function renderBacklogList(
  overrides: Partial<Parameters<typeof BacklogList>[0]> = {},
) {
  return render(
    <BacklogList
      activeGames={[activeGame]}
      completedGames={[]}
      onToggleCompleted={noop}
      onRemoveGame={noop}
      updatingBacklogGameId={null}
      {...overrides}
    />,
  );
}

describe("BacklogList", () => {
  test("renders active games section header", () => {
    renderBacklogList();
    expect(screen.getByText("Active Backlog")).toBeInTheDocument();
  });

  test("renders active game count", () => {
    renderBacklogList({ activeGames: [activeGame] });
    expect(screen.getByText("1 game to work through")).toBeInTheDocument();
  });

  test("renders pluralized game count", () => {
    const game2 = { ...activeGame, backlogGameId: 3, title: "Game 2" };
    renderBacklogList({ activeGames: [activeGame, game2] });
    expect(screen.getByText("2 games to work through")).toBeInTheDocument();
  });

  test("renders game title", () => {
    renderBacklogList();
    expect(screen.getByText("Active Game")).toBeInTheDocument();
  });

  test("renders time to beat", () => {
    renderBacklogList();
    expect(screen.getByText("⏱️ 10h")).toBeInTheDocument();
  });

  test("renders rating", () => {
    renderBacklogList();
    expect(screen.getByText("⭐ 85/100")).toBeInTheDocument();
  });

  test("renders genre chips", () => {
    renderBacklogList();
    expect(screen.getByText("Action")).toBeInTheDocument();
  });

  test("renders Mark complete button for active game", () => {
    renderBacklogList();
    expect(
      screen.getByRole("button", { name: /mark complete/i }),
    ).toBeInTheDocument();
  });

  test("renders delete button for active game", () => {
    renderBacklogList();
    expect(
      screen.getByRole("button", { name: /remove from backlog/i }),
    ).toBeInTheDocument();
  });

  test("calls onToggleCompleted when Mark complete is clicked", () => {
    const onToggleCompleted = vi.fn();
    renderBacklogList({ onToggleCompleted });
    fireEvent.click(screen.getByRole("button", { name: /mark complete/i }));
    expect(onToggleCompleted).toHaveBeenCalledWith(activeGame);
  });

  test("opens remove dialog when delete button is clicked", () => {
    renderBacklogList();
    fireEvent.click(
      screen.getByRole("button", { name: /remove from backlog/i }),
    );
    expect(screen.getByText("Remove game from backlog?")).toBeInTheDocument();
    expect(
      screen.getByText(/Remove Active Game from your backlog/),
    ).toBeInTheDocument();
  });

  test("calls onRemoveGame when remove is confirmed", () => {
    const onRemoveGame = vi.fn();
    renderBacklogList({ onRemoveGame });
    fireEvent.click(
      screen.getByRole("button", { name: /remove from backlog/i }),
    );
    fireEvent.click(screen.getByRole("button", { name: /^remove$/i }));
    expect(onRemoveGame).toHaveBeenCalledWith(activeGame);
  });

  test("closes dialog when cancel is clicked", () => {
    renderBacklogList();
    fireEvent.click(
      screen.getByRole("button", { name: /remove from backlog/i }),
    );
    expect(screen.getByText("Remove game from backlog?")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(screen.getByText("Remove game from backlog?")).not.toBeVisible();
  });

  test("does not render completed section when no completed games", () => {
    renderBacklogList({ completedGames: [] });
    expect(screen.queryByText("Completed Games")).not.toBeInTheDocument();
  });

  test("renders completed games section when completed games exist", () => {
    renderBacklogList({ completedGames: [completedGame] });
    expect(screen.getByText("Completed Games")).toBeInTheDocument();
    expect(screen.getByText("Completed Game")).toBeInTheDocument();
  });

  test("renders Completed chip for completed games", () => {
    renderBacklogList({ completedGames: [completedGame] });
    expect(screen.getAllByText("Completed").length).toBeGreaterThanOrEqual(1);
  });

  test("renders Completed button for completed games", () => {
    renderBacklogList({ completedGames: [completedGame] });
    expect(
      screen.getAllByRole("button", { name: /completed/i }).length,
    ).toBeGreaterThanOrEqual(1);
  });

  test("shows Jump to completed games button when completed games exist", () => {
    renderBacklogList({ completedGames: [completedGame] });
    expect(
      screen.getByRole("button", { name: /jump to completed games/i }),
    ).toBeInTheDocument();
  });

  test("does not show Jump to completed games button when no completed games", () => {
    renderBacklogList({ completedGames: [] });
    expect(
      screen.queryByRole("button", { name: /jump to completed games/i }),
    ).not.toBeInTheDocument();
  });

  test("disables buttons when game is being updated", () => {
    renderBacklogList({ updatingBacklogGameId: 1 });
    expect(
      screen.getByRole("button", { name: /mark complete/i }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: /remove from backlog/i }),
    ).toBeDisabled();
  });

  test("renders dividers between items", () => {
    const game2 = { ...activeGame, backlogGameId: 3, title: "Game 2" };
    const { container } = renderBacklogList({
      activeGames: [activeGame, game2],
    });
    const dividers = container.querySelectorAll("hr");
    expect(dividers.length).toBeGreaterThanOrEqual(1);
  });

  test("renders completed game count with singular form", () => {
    renderBacklogList({ completedGames: [completedGame] });
    expect(screen.getByText("1 completed game")).toBeInTheDocument();
  });

  test("renders completed game count with plural form", () => {
    const game2 = { ...completedGame, backlogGameId: 4, title: "Game 2" };
    renderBacklogList({ completedGames: [completedGame, game2] });
    expect(screen.getByText("2 completed games")).toBeInTheDocument();
  });

  test("shows Jump to top of backlog button in completed section", () => {
    renderBacklogList({ completedGames: [completedGame] });
    expect(
      screen.getByRole("button", { name: /jump to top of backlog/i }),
    ).toBeInTheDocument();
  });

  test("scrolls to completed games when jump button is clicked", () => {
    const scrollIntoView = vi.fn();
    const completedSection = document.createElement("div");
    completedSection.id = "completed-games";
    vi.spyOn(document, "getElementById").mockReturnValue(completedSection);
    completedSection.scrollIntoView = scrollIntoView;

    renderBacklogList({ completedGames: [completedGame] });
    fireEvent.click(
      screen.getByRole("button", { name: /jump to completed games/i }),
    );
    expect(scrollIntoView).toHaveBeenCalledWith({
      behavior: "smooth",
      block: "start",
    });

    vi.restoreAllMocks();
  });

  test("scrolls to top of backlog when jump button is clicked", () => {
    const scrollTo = vi.fn();
    vi.spyOn(window, "scrollTo").mockImplementation(scrollTo);

    renderBacklogList({ completedGames: [completedGame] });
    fireEvent.click(
      screen.getByRole("button", { name: /jump to top of backlog/i }),
    );
    expect(scrollTo).toHaveBeenCalledWith({ top: 0, behavior: "smooth" });

    vi.restoreAllMocks();
  });

  test("calls onRemoveGame when removing a completed game", () => {
    const onRemoveGame = vi.fn();
    renderBacklogList({
      completedGames: [completedGame],
      onRemoveGame,
    });
    const removeButtons = screen.getAllByRole("button", {
      name: /remove from backlog/i,
    });
    fireEvent.click(removeButtons[removeButtons.length - 1]);
    fireEvent.click(screen.getByRole("button", { name: /^remove$/i }));
    expect(onRemoveGame).toHaveBeenCalledWith(completedGame);
  });
});
