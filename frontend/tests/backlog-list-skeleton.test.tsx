import { renderToStaticMarkup } from "react-dom/server";

import { BacklogListSkeleton } from "../src/pages/my-backlog/BacklogListSkeleton";

function renderSkeleton() {
  return renderToStaticMarkup(<BacklogListSkeleton />);
}

describe("BacklogListSkeleton", () => {
  test("renders skeleton elements", () => {
    const markup = renderSkeleton();
    expect(markup).toContain("MuiSkeleton");
  });

  test("renders 6 skeleton rows", () => {
    const markup = renderSkeleton();
    const listItems = markup.split("<li");
    expect(listItems.length - 1).toBe(6);
  });

  test("renders single Paper container", () => {
    const markup = renderSkeleton();
    expect(markup).toContain("MuiPaper-elevation2");
  });

  test("renders action button skeletons for rows", () => {
    const markup = renderSkeleton();
    expect(markup).toContain("width:110px");
    expect(markup).toContain("width:40px");
  });

  test("renders dividers between rows", () => {
    const markup = renderSkeleton();
    const dividers = markup.split("<hr");
    expect(dividers.length - 1).toBe(5);
  });

  test("renders time and rating skeleton placeholders", () => {
    const markup = renderSkeleton();
    expect(markup).toContain("width:40px");
    expect(markup).toContain("width:55px");
  });

  test("renders genre chip skeleton placeholders", () => {
    const markup = renderSkeleton();
    const chipSkeletons = markup.split("width:60px");
    expect(chipSkeletons.length - 1).toBeGreaterThanOrEqual(3);
  });
});
