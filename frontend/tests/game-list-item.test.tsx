import { render, screen, fireEvent } from "@testing-library/react";

import type { GameSearchRow } from "../src/client";
import { GameListItem } from "../src/pages/games/GameListItem";

const defaultGame: GameSearchRow = {
  gameId: 1,
  title: "Test Game",
  totalRating: 85,
  timeToBeat: 14400,
  genres: [],
  coverImageId: null,
};
const noop = () => {};

function renderGameListItem(
  overrides: Partial<Parameters<typeof GameListItem>[0]> = {},
) {
  return render(
    <GameListItem
      addingInProgress={false}
      game={defaultGame}
      hasBacklog={false}
      inBacklog={false}
      isLast={false}
      isLoggedIn={false}
      onAddToBacklog={noop}
      {...overrides}
    />,
  );
}

describe("GameListItem", () => {
  test("renders the game title", () => {
    renderGameListItem();
    expect(screen.getByText("Test Game")).toBeInTheDocument();
  });

  test("renders the rating when available", () => {
    renderGameListItem();
    expect(screen.getByText("85/100 rating")).toBeInTheDocument();
  });

  test('renders "Rating unavailable" when rating is null', () => {
    renderGameListItem({
      game: { ...defaultGame, totalRating: null },
    });
    expect(screen.getByText("Rating unavailable")).toBeInTheDocument();
  });

  test("renders the time to beat when available", () => {
    renderGameListItem();
    expect(screen.getByText("4h to beat")).toBeInTheDocument();
  });

  test('renders "Time to beat unavailable" when timeToBeat is null', () => {
    renderGameListItem({
      game: { ...defaultGame, timeToBeat: null },
    });
    expect(screen.getByText("Time to beat unavailable")).toBeInTheDocument();
  });

  test("renders no secondary action when not logged in", () => {
    renderGameListItem({ isLoggedIn: false });
    expect(screen.queryByText("In backlog")).not.toBeInTheDocument();
    expect(screen.queryByText("Add to backlog")).not.toBeInTheDocument();
  });

  test("renders no secondary action when logged in but no backlog", () => {
    renderGameListItem({
      isLoggedIn: true,
      hasBacklog: false,
    });
    expect(screen.queryByText("In backlog")).not.toBeInTheDocument();
    expect(screen.queryByText("Add to backlog")).not.toBeInTheDocument();
  });

  test('renders "In backlog" chip when game is in backlog', () => {
    renderGameListItem({
      isLoggedIn: true,
      hasBacklog: true,
      inBacklog: true,
    });
    expect(screen.getByText("In backlog")).toBeInTheDocument();
  });

  test('renders "Add to backlog" button when game can be added', () => {
    renderGameListItem({
      isLoggedIn: true,
      hasBacklog: true,
      inBacklog: false,
    });
    expect(
      screen.getByRole("button", { name: /add to backlog/i }),
    ).toBeInTheDocument();
  });

  test('renders "Adding…" when add is in progress', () => {
    renderGameListItem({
      addingInProgress: true,
      isLoggedIn: true,
      hasBacklog: true,
      inBacklog: false,
    });
    expect(screen.getByText("Adding…")).toBeInTheDocument();
  });

  test("renders a divider when not the last item", () => {
    const { container } = renderGameListItem({ isLast: false });
    expect(container.querySelector("hr")).toBeInTheDocument();
  });

  test("does not render a divider when is the last item", () => {
    const { container } = renderGameListItem({ isLast: true });
    expect(container.querySelector("hr")).not.toBeInTheDocument();
  });

  test("renders genre chips when genres are provided", () => {
    renderGameListItem({
      game: { ...defaultGame, genres: ["Action", "Roguelike"] },
    });
    expect(screen.getByText("Action")).toBeInTheDocument();
    expect(screen.getByText("Roguelike")).toBeInTheDocument();
  });

  test("renders no genre chips when genres are empty", () => {
    renderGameListItem({ game: { ...defaultGame, genres: [] } });
    expect(screen.queryByRole("button", { name: /action/i })).toBeNull();
  });

  test("renders overflow chip when more than 3 genres", () => {
    renderGameListItem({
      game: {
        ...defaultGame,
        genres: ["Action", "RPG", "Adventure", "Strategy"],
      },
    });
    expect(screen.getByText("Action")).toBeInTheDocument();
    expect(screen.getByText("RPG")).toBeInTheDocument();
    expect(screen.getByText("Adventure")).toBeInTheDocument();
    expect(screen.getByText("+1")).toBeInTheDocument();
    expect(screen.queryByText("Strategy")).toBeNull();
  });

  test("calls onAddToBacklog when add button is clicked", () => {
    const onAddToBacklog = vi.fn();
    renderGameListItem({
      isLoggedIn: true,
      hasBacklog: true,
      inBacklog: false,
      onAddToBacklog,
    });

    fireEvent.click(screen.getByRole("button", { name: /add to backlog/i }));
    expect(onAddToBacklog).toHaveBeenCalledWith(defaultGame.gameId);
  });
});
