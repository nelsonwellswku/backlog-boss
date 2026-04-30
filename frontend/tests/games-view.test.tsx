import type { ComponentProps, FormEventHandler } from "react";
import { renderToStaticMarkup } from "react-dom/server";

import type { GameSearchRow } from "../src/client";
import { GamesView } from "../src/pages/games/GamesView";

const noop: FormEventHandler<HTMLFormElement> = () => {};
const noopQueryChange = () => {};

function renderGamesView(overrides: Partial<ComponentProps<typeof GamesView>> = {}) {
  return renderToStaticMarkup(
    <GamesView
      errorMessage={null}
      hasSearched={false}
      isError={false}
      isPending={false}
      onQueryChange={noopQueryChange}
      onSearch={noop}
      query=""
      results={[]}
      submittedQuery=""
      {...overrides}
    />,
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
    expect(markup).toContain('Searching for &quot;hades&quot;');
  });

  test("renders formatted results", () => {
    const results: GameSearchRow[] = [
      {
        gameId: 44,
        title: "Hades II",
        totalRating: 93.5,
        timeToBeat: 43200,
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

    expect(markup).toContain('No games found for &quot;unknown game&quot;.');
  });
});
