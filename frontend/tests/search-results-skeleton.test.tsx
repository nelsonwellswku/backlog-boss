import { renderToStaticMarkup } from "react-dom/server";

import { SearchResultsSkeleton } from "../src/pages/games/SearchResultsSkeleton";

function renderSkeleton(query = "hades") {
  return renderToStaticMarkup(
    <SearchResultsSkeleton submittedQuery={query} />,
  );
}

describe("SearchResultsSkeleton", () => {
  test("renders the searching header with query", () => {
    const markup = renderSkeleton("hades");
    expect(markup).toContain("Searching for &quot;hades&quot;");
  });

  test("renders the subtitle text", () => {
    const markup = renderSkeleton();
    expect(markup).toContain("Pulling matching games");
  });

  test("renders 5 skeleton list items", () => {
    const markup = renderSkeleton();
    const listItems = markup.split("<li");
    expect(listItems.length - 1).toBe(5);
  });

  test("renders title skeleton placeholders", () => {
    const markup = renderSkeleton();
    expect(markup).toContain("width:40%");
  });

  test("renders chip skeleton placeholders", () => {
    const markup = renderSkeleton();
    expect(markup).toContain("width:90px");
    expect(markup).toContain("width:80px");
  });

  test("renders add button skeleton placeholders", () => {
    const markup = renderSkeleton();
    expect(markup).toContain("width:120px");
  });

  test("renders dividers between items except last", () => {
    const markup = renderSkeleton();
    const dividers = markup.split("<hr");
    expect(dividers.length - 1).toBe(4);
  });

  test("renders with different query", () => {
    const markup = renderSkeleton("zelda");
    expect(markup).toContain("Searching for &quot;zelda&quot;");
  });
});
