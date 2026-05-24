import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router";
import { describe, expect, test } from "vitest";

import type { GameSearchRow } from "../src/client";
import { GameResultItem } from "../src/pages/games/GameResultItem";
import { NoBacklogAlert } from "../src/pages/games/NoBacklogAlert";
import { NoResultsAlert } from "../src/pages/games/NoResultsAlert";
import { SearchInstructions } from "../src/pages/games/SearchInstructions";
import { SearchLoadingState } from "../src/pages/games/SearchLoadingState";
import { SearchResults } from "../src/pages/games/SearchResults";

function renderInRouter(component: React.ReactNode) {
  return renderToStaticMarkup(
    <MemoryRouter>{component}</MemoryRouter>,
  );
}

describe("SearchInstructions", () => {
  test("renders search instructions", () => {
    const markup = renderToStaticMarkup(<SearchInstructions />);
    expect(markup).toContain("Search by title");
  });
});

describe("SearchLoadingState", () => {
  test("renders loading state with query", () => {
    const markup = renderToStaticMarkup(
      <SearchLoadingState submittedQuery="hades" />,
    );
    expect(markup).toContain("Searching for");
    expect(markup).toContain("hades");
  });
});

describe("NoResultsAlert", () => {
  test("renders no results message", () => {
    const markup = renderToStaticMarkup(
      <NoResultsAlert submittedQuery="unknown game" />,
    );
    expect(markup).toContain("No games found for");
    expect(markup).toContain("unknown game");
  });
});

describe("NoBacklogAlert", () => {
  test("renders create backlog alert", () => {
    const markup = renderInRouter(<NoBacklogAlert />);
    expect(markup).toContain("Create your backlog");
    expect(markup).toContain("have a backlog yet");
  });
});

describe("SearchResults", () => {
  const results: GameSearchRow[] = [
    { gameId: 44, title: "Hades II", totalRating: 93.5, timeToBeat: 43200 },
  ];

  test("renders formatted results", () => {
    const markup = renderToStaticMarkup(
      <SearchResults
        results={results}
        submittedQuery="hades"
        backlogGameIds={new Set()}
        addedGameIds={new Set()}
        addingGameId={null}
        isLoggedIn={true}
        hasBacklog={true}
        onAddToBacklog={() => {}}
      />,
    );
    expect(markup).toContain("Search Results");
    expect(markup).toContain("Hades II");
    expect(markup).toContain("94/100 rating");
    expect(markup).toContain("12h to beat");
  });

  test('shows "Add to backlog" button when logged in', () => {
    const markup = renderToStaticMarkup(
      <SearchResults
        results={results}
        submittedQuery="hades"
        backlogGameIds={new Set()}
        addedGameIds={new Set()}
        addingGameId={null}
        isLoggedIn={true}
        hasBacklog={true}
        onAddToBacklog={() => {}}
      />,
    );
    expect(markup).toContain("Add to backlog");
  });

  test('shows "In backlog" chip for game already in backlog', () => {
    const markup = renderToStaticMarkup(
      <SearchResults
        results={results}
        submittedQuery="hades"
        backlogGameIds={new Set([44])}
        addedGameIds={new Set()}
        addingGameId={null}
        isLoggedIn={true}
        hasBacklog={true}
        onAddToBacklog={() => {}}
      />,
    );
    expect(markup).toContain("In backlog");
  });

  test('shows "Adding…" while game is being added', () => {
    const markup = renderToStaticMarkup(
      <SearchResults
        results={results}
        submittedQuery="hades"
        backlogGameIds={new Set()}
        addedGameIds={new Set()}
        addingGameId={44}
        isLoggedIn={true}
        hasBacklog={true}
        onAddToBacklog={() => {}}
      />,
    );
    expect(markup).toContain("Adding…");
  });

  test('hides add button when not logged in', () => {
    const markup = renderToStaticMarkup(
      <SearchResults
        results={results}
        submittedQuery="hades"
        backlogGameIds={new Set()}
        addedGameIds={new Set()}
        addingGameId={null}
        isLoggedIn={false}
        hasBacklog={false}
        onAddToBacklog={() => {}}
      />,
    );
    expect(markup).not.toContain("Add to backlog");
  });
});

describe("GameResultItem", () => {
  const game: GameSearchRow = {
    gameId: 1,
    title: "Hades",
    totalRating: 91,
    timeToBeat: 36000,
  };

  test("renders game title and stats", () => {
    const markup = renderToStaticMarkup(
      <GameResultItem
        game={game}
        isInBacklog={false}
        isRecentlyAdded={false}
        isAdding={false}
        canAdd={false}
        onAdd={() => {}}
      />,
    );
    expect(markup).toContain("Hades");
    expect(markup).toContain("91/100 rating");
    expect(markup).toContain("10h to beat");
  });

  test("shows add button when canAdd", () => {
    const markup = renderToStaticMarkup(
      <GameResultItem
        game={game}
        isInBacklog={false}
        isRecentlyAdded={false}
        isAdding={false}
        canAdd={true}
        onAdd={() => {}}
      />,
    );
    expect(markup).toContain("Add to backlog");
  });

  test("shows In backlog chip when isInBacklog", () => {
    const markup = renderToStaticMarkup(
      <GameResultItem
        game={game}
        isInBacklog={true}
        isRecentlyAdded={false}
        isAdding={false}
        canAdd={true}
        onAdd={() => {}}
      />,
    );
    expect(markup).toContain("In backlog");
  });

  test("shows In backlog chip when isRecentlyAdded", () => {
    const markup = renderToStaticMarkup(
      <GameResultItem
        game={game}
        isInBacklog={false}
        isRecentlyAdded={true}
        isAdding={false}
        canAdd={true}
        onAdd={() => {}}
      />,
    );
    expect(markup).toContain("In backlog");
  });
});
