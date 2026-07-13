import type { ComponentProps, SubmitEventHandler } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router";

import type { GameSearchRow } from "../src/client";
import { GamesView } from "../src/pages/games/GamesView";

const noop: SubmitEventHandler<HTMLFormElement> = () => {};
const noopQueryChange = () => {};
const noopAddToBacklog = () => {};

function renderGamesView(
  overrides: Partial<ComponentProps<typeof GamesView>> = {},
) {
  return renderToStaticMarkup(
    <MemoryRouter>
      <GamesView
        addedGameIds={new Set()}
        addingGameId={null}
        backlogGameIds={new Set()}
        errorMessage={null}
        hasBacklog={false}
        hasSearched={false}
        isBacklogLoading={false}
        isError={false}
        isLoggedIn={false}
        isPending={false}
        onAddToBacklog={noopAddToBacklog}
        onQueryChange={noopQueryChange}
        onSearch={noop}
        query=""
        results={[]}
        submittedQuery=""
        {...overrides}
      />
    </MemoryRouter>,
  );
}

describe("GamesView", () => {
  test("renders the search page shell", () => {
    const markup = renderGamesView();

    expect(markup).toContain("Discover Games");
    expect(markup).toContain("Game name");
    expect(markup).toContain("Search by title");
  });

  test("renders the loading state after a search starts", () => {
    const markup = renderGamesView({
      hasSearched: true,
      isPending: true,
      submittedQuery: "hades",
      query: "hades",
    });

    expect(markup).toContain("Searching…");
    expect(markup).toContain("Searching for &quot;hades&quot;");
  });

  test("renders formatted results", () => {
    const results: GameSearchRow[] = [
      {
        gameId: 44,
        title: "Hades II",
        totalRating: 93.5,
        timeToBeat: 43200,
        genres: [],
        coverImageId: null,
      },
    ];

    const markup = renderGamesView({
      hasSearched: true,
      results,
      submittedQuery: "hades",
    });

    expect(markup).toContain("Search Results");
    expect(markup).toContain("Hades II");
    expect(markup).toContain("94/100 rating");
    expect(markup).toContain("12h to beat");
  });

  test("renders the empty state when nothing matches", () => {
    const markup = renderGamesView({
      hasSearched: true,
      results: [],
      submittedQuery: "unknown game",
    });

    expect(markup).toContain("No games found for &quot;unknown game&quot;.");
  });

  test('shows "Create your backlog" alert when logged in but no backlog', () => {
    const markup = renderGamesView({
      isLoggedIn: true,
      hasBacklog: false,
      isBacklogLoading: false,
    });

    expect(markup).toContain("Create your backlog");
    expect(markup).toContain("have a backlog yet");
  });

  test('shows "Add to backlog" button when logged in and results are present', () => {
    const results: GameSearchRow[] = [
      {
        gameId: 1,
        title: "Hades",
        totalRating: 91,
        timeToBeat: 36000,
        genres: [],
        coverImageId: null,
      },
    ];

    const markup = renderGamesView({
      hasSearched: true,
      isLoggedIn: true,
      hasBacklog: true,
      results,
    });

    expect(markup).toContain("Add to backlog");
  });

  test('shows "In backlog" chip for a game already in the backlog', () => {
    const results: GameSearchRow[] = [
      {
        gameId: 1,
        title: "Hades",
        totalRating: 91,
        timeToBeat: 36000,
        genres: [],
        coverImageId: null,
      },
    ];

    const markup = renderGamesView({
      hasSearched: true,
      isLoggedIn: true,
      hasBacklog: true,
      backlogGameIds: new Set([1]),
      results,
    });

    expect(markup).toContain("In backlog");
  });

  test('shows "Adding…" button while a game is being added', () => {
    const results: GameSearchRow[] = [
      {
        gameId: 1,
        title: "Hades",
        totalRating: 91,
        timeToBeat: 36000,
        genres: [],
        coverImageId: null,
      },
    ];

    const markup = renderGamesView({
      hasSearched: true,
      isLoggedIn: true,
      hasBacklog: true,
      addingGameId: 1,
      results,
    });

    expect(markup).toContain("Adding…");
  });

  test("renders error alert when search errors and no custom message", () => {
    const markup = renderGamesView({
      isError: true,
      errorMessage: null,
    });

    expect(markup).toContain(
      "We couldn&#x27;t search for games right now. Please try again.",
    );
  });

  test("renders custom error message when provided", () => {
    const markup = renderGamesView({
      isError: true,
      errorMessage: "Custom error message",
    });

    expect(markup).toContain("Custom error message");
  });

  test("renders genre chips for search results", () => {
    const results: GameSearchRow[] = [
      {
        gameId: 1,
        title: "Hades",
        totalRating: 91,
        timeToBeat: 36000,
        genres: ["Action", "Roguelike"],
        coverImageId: null,
      },
    ];

    const markup = renderGamesView({
      hasSearched: true,
      results,
    });

    expect(markup).toContain("Action");
    expect(markup).toContain("Roguelike");
  });

  test("renders multiple results with pluralized text", () => {
    const results: GameSearchRow[] = [
      {
        gameId: 1,
        title: "Hades",
        totalRating: 91,
        timeToBeat: 36000,
        genres: [],
        coverImageId: null,
      },
      {
        gameId: 2,
        title: "Hades II",
        totalRating: 93,
        timeToBeat: 43200,
        genres: [],
        coverImageId: null,
      },
    ];

    const markup = renderGamesView({
      hasSearched: true,
      results,
      submittedQuery: "hades",
    });

    expect(markup).toContain("2 games matching");
  });
});
