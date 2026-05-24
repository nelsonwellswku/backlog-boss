import { render, screen, fireEvent } from "@testing-library/react";
import type { SubmitEventHandler } from "react";

import { SearchForm } from "../src/pages/games/SearchForm";

const noopHandler: SubmitEventHandler<HTMLFormElement> = () => {};
const noopQueryChange = () => {};

function renderSearchForm(
  overrides: Partial<Parameters<typeof SearchForm>[0]> = {},
) {
  return render(
    <SearchForm
      isPending={false}
      onQueryChange={noopQueryChange}
      onSearch={noopHandler}
      query=""
      {...overrides}
    />,
  );
}

describe("SearchForm", () => {
  test("renders the search field and button", () => {
    renderSearchForm();
    expect(screen.getByLabelText("Game name")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /search/i })).toBeInTheDocument();
  });

  test("search button is disabled when query is empty", () => {
    renderSearchForm({ query: "" });
    expect(screen.getByRole("button", { name: /search/i })).toBeDisabled();
  });

  test("search button is enabled when query has text", () => {
    renderSearchForm({ query: "hades" });
    expect(screen.getByRole("button", { name: /search/i })).toBeEnabled();
  });

  test("search button is disabled when request is pending", () => {
    renderSearchForm({ query: "hades", isPending: true });
    expect(screen.getByRole("button", { name: /search/i })).toBeDisabled();
  });

  test('shows "Searching…" and spinner when pending', () => {
    const { container } = renderSearchForm({
      query: "hades",
      isPending: true,
    });
    expect(screen.getByText("Searching…")).toBeInTheDocument();
    expect(
      container.querySelector(".MuiCircularProgress-root"),
    ).toBeInTheDocument();
  });

  test("shows search icon when not pending", () => {
    const { container } = renderSearchForm({
      query: "hades",
      isPending: false,
    });
    expect(
      container.querySelector('[data-testid="SearchIcon"]'),
    ).toBeInTheDocument();
  });

  test("calls onQueryChange when text is typed", () => {
    const onQueryChange = vi.fn();
    renderSearchForm({ onQueryChange });

    fireEvent.change(screen.getByLabelText("Game name"), {
      target: { value: "Hades" },
    });
    expect(onQueryChange).toHaveBeenCalledWith("Hades");
  });

  test("calls onSearch when form is submitted", () => {
    const onSearch = vi.fn();
    renderSearchForm({ query: "Hades", onSearch });

    fireEvent.submit(
      screen.getByRole("button", { name: /search/i }).closest("form")!,
    );
    expect(onSearch).toHaveBeenCalled();
  });
});
