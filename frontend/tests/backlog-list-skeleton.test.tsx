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

  test("renders 6 active skeleton rows", () => {
    const markup = renderSkeleton();
    const listItems = markup.split("<li");
    expect(listItems.length - 1).toBe(8);
  });

  test("renders completed games section", () => {
    const markup = renderSkeleton();
    expect(markup).toContain("MuiPaper-elevation1");
  });

  test("renders action button skeletons for active rows", () => {
    const markup = renderSkeleton();
    expect(markup).toContain("width:110px");
    expect(markup).toContain("width:40px");
  });

  test("renders dividers between active rows", () => {
    const markup = renderSkeleton();
    const dividers = markup.split("<hr");
    expect(dividers.length - 1).toBe(6);
  });

  test("renders title skeleton placeholders", () => {
    const markup = renderSkeleton();
    expect(markup).toContain("width:180px");
    expect(markup).toContain("width:200px");
  });

  test("renders subtitle skeleton placeholders", () => {
    const markup = renderSkeleton();
    expect(markup).toContain("width:140px");
    expect(markup).toContain("width:160px");
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
