import { render, screen } from "@testing-library/react";

import type { GameSearchRow } from "../src/client";
import { SearchResults } from "../src/pages/games/SearchResults";

const noop = () => {};

const game: GameSearchRow = {
  gameId: 1,
  title: "Hades",
  totalRating: 91,
  timeToBeat: 36000,
  genres: ["Action", "Roguelike"],
  coverImageId: null,
};

function renderSearchResults(
  overrides: Partial<Parameters<typeof SearchResults>[0]> = {},
) {
  return render(
    <SearchResults
      addedGameIds={new Set()}
      addingGameId={null}
      backlogGameIds={new Set()}
      hasBacklog={true}
      isLoggedIn={true}
      onAddToBacklog={noop}
      results={[game]}
      submittedQuery="hades"
      {...overrides}
    />,
  );
}

describe("SearchResults", () => {
  test("renders empty state when no results", () => {
    renderSearchResults({ results: [] });
    expect(screen.getByText('No games found for "hades".')).toBeInTheDocument();
  });

  test("renders Search Results header", () => {
    renderSearchResults();
    expect(screen.getByText("Search Results")).toBeInTheDocument();
  });

  test("renders result count with singular form", () => {
    renderSearchResults({ results: [game] });
    expect(screen.getByText('1 game matching "hades"')).toBeInTheDocument();
  });

  test("renders result count with plural form", () => {
    const game2 = { ...game, gameId: 2, title: "Hades II" };
    renderSearchResults({ results: [game, game2] });
    expect(screen.getByText('2 games matching "hades"')).toBeInTheDocument();
  });

  test("renders game title", () => {
    renderSearchResults();
    expect(screen.getByText("Hades")).toBeInTheDocument();
  });

  test("renders Add to backlog button when logged in with backlog", () => {
    renderSearchResults({
      isLoggedIn: true,
      hasBacklog: true,
    });
    expect(
      screen.getByRole("button", { name: /add to backlog/i }),
    ).toBeInTheDocument();
  });

  test("does not render Add to backlog button when not logged in", () => {
    renderSearchResults({ isLoggedIn: false });
    expect(
      screen.queryByRole("button", { name: /add to backlog/i }),
    ).not.toBeInTheDocument();
  });

  test("does not render Add to backlog button when no backlog", () => {
    renderSearchResults({ isLoggedIn: true, hasBacklog: false });
    expect(
      screen.queryByRole("button", { name: /add to backlog/i }),
    ).not.toBeInTheDocument();
  });

  test("renders In backlog chip for game already in backlog", () => {
    renderSearchResults({
      backlogGameIds: new Set([1]),
    });
    expect(screen.getByText("In backlog")).toBeInTheDocument();
  });

  test("renders In backlog chip for game recently added", () => {
    renderSearchResults({
      addedGameIds: new Set([1]),
    });
    expect(screen.getByText("In backlog")).toBeInTheDocument();
  });

  test("renders Adding… when game is being added", () => {
    renderSearchResults({
      addingGameId: 1,
    });
    expect(screen.getByText("Adding…")).toBeInTheDocument();
  });

  test("renders genre chips for results", () => {
    renderSearchResults();
    expect(screen.getByText("Action")).toBeInTheDocument();
    expect(screen.getByText("Roguelike")).toBeInTheDocument();
  });

  test("renders rating chip", () => {
    renderSearchResults();
    expect(screen.getByText("91/100 rating")).toBeInTheDocument();
  });

  test("renders time to beat chip", () => {
    renderSearchResults();
    expect(screen.getByText("10h to beat")).toBeInTheDocument();
  });
});
