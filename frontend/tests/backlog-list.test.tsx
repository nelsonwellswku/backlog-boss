import { render, screen, fireEvent } from "@testing-library/react";

import type { BacklogGameRow } from "../src/client";
import { BacklogTabContent } from "../src/pages/my-backlog/BacklogTabContent";

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

function renderTabContent(
  overrides: Partial<Parameters<typeof BacklogTabContent>[0]> = {},
) {
  return render(
    <BacklogTabContent
      games={[activeGame]}
      completedInSessionSet={new Set()}
      onToggleCompleted={noop}
      onRemoveGame={noop}
      updatingBacklogGameId={null}
      emptyMessage="No games in your backlog yet."
      {...overrides}
    />,
  );
}

describe("BacklogTabContent", () => {
  test("renders game title", () => {
    renderTabContent();
    expect(screen.getByText("Active Game")).toBeInTheDocument();
  });

  test("renders Steam store link when steamAppId is present", () => {
    renderTabContent();
    const link = screen.getByRole("link", {
      name: /open in steam/i,
    });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute(
      "href",
      "https://store.steampowered.com/app/1000",
    );
    expect(link).toHaveAttribute("target", "_blank");
  });

  test("does not render Steam store link when steamAppId is null", () => {
    const gameNoSteam = { ...activeGame, steamAppId: null };
    renderTabContent({ games: [gameNoSteam] });
    expect(
      screen.queryByRole("link", { name: /open in steam/i }),
    ).not.toBeInTheDocument();
  });

  test("renders time to beat", () => {
    renderTabContent();
    expect(screen.getByText("⏱️ 10h")).toBeInTheDocument();
  });

  test("renders rating", () => {
    renderTabContent();
    expect(screen.getByText("⭐ 85/100")).toBeInTheDocument();
  });

  test("renders genre chips", () => {
    renderTabContent();
    expect(screen.getByText("Action")).toBeInTheDocument();
  });

  test("renders Mark complete button for active game", () => {
    renderTabContent();
    expect(
      screen.getByRole("button", { name: /mark complete/i }),
    ).toBeInTheDocument();
  });

  test("renders delete button for active game", () => {
    renderTabContent();
    expect(
      screen.getByRole("button", { name: /remove from backlog/i }),
    ).toBeInTheDocument();
  });

  test("calls onToggleCompleted when Mark complete is clicked", () => {
    const onToggleCompleted = vi.fn();
    renderTabContent({ onToggleCompleted });
    fireEvent.click(screen.getByRole("button", { name: /mark complete/i }));
    expect(onToggleCompleted).toHaveBeenCalledWith(activeGame);
  });

  test("opens remove dialog when delete button is clicked", () => {
    renderTabContent();
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
    renderTabContent({ onRemoveGame });
    fireEvent.click(
      screen.getByRole("button", { name: /remove from backlog/i }),
    );
    fireEvent.click(screen.getByRole("button", { name: /^remove$/i }));
    expect(onRemoveGame).toHaveBeenCalledWith(activeGame);
  });

  test("closes dialog when cancel is clicked", () => {
    renderTabContent();
    fireEvent.click(
      screen.getByRole("button", { name: /remove from backlog/i }),
    );
    expect(screen.getByText("Remove game from backlog?")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(screen.getByText("Remove game from backlog?")).not.toBeVisible();
  });

  test("shows empty message when no games", () => {
    renderTabContent({ games: [], emptyMessage: "No games yet." });
    expect(screen.getByText("No games yet.")).toBeInTheDocument();
  });

  test("does not show empty message when games exist", () => {
    renderTabContent({ emptyMessage: "No games yet." });
    expect(screen.queryByText("No games yet.")).not.toBeInTheDocument();
  });

  test("shows completed visual cue for completed games", () => {
    renderTabContent({ games: [completedGame] });
    expect(screen.getByText("Completed Game")).toBeInTheDocument();
    expect(screen.getAllByText("Completed").length).toBeGreaterThanOrEqual(1);
  });

  test("shows completed cue for games in completedInSessionSet", () => {
    renderTabContent({
      games: [activeGame],
      completedInSessionSet: new Set([activeGame.backlogGameId]),
    });
    expect(screen.getAllByText("Completed").length).toBeGreaterThanOrEqual(1);
  });

  test("disables buttons when game is being updated", () => {
    renderTabContent({ updatingBacklogGameId: 1 });
    expect(
      screen.getByRole("button", { name: /mark complete/i }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: /remove from backlog/i }),
    ).toBeDisabled();
  });

  test("renders dividers between items", () => {
    const game2 = { ...activeGame, backlogGameId: 3, title: "Game 2" };
    const { container } = renderTabContent({
      games: [activeGame, game2],
    });
    const dividers = container.querySelectorAll("hr");
    expect(dividers.length).toBeGreaterThanOrEqual(1);
  });
});
