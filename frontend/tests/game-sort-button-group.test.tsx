import { render, screen, fireEvent } from "@testing-library/react";
import { vi, describe, test, expect } from "vitest";

import { GameSortButtonGroup } from "../src/pages/my-backlog/GameSortButtonGroup";

function renderSortButtonGroup(
  overrides: Partial<Parameters<typeof GameSortButtonGroup>[0]> = {},
) {
  const setSortType = vi.fn();
  return {
    setSortType,
    ...render(
      <GameSortButtonGroup sortType="score" setSortType={setSortType} {...overrides} />,
    ),
  };
}

describe("GameSortButtonGroup", () => {
  test("renders three sort buttons", () => {
    renderSortButtonGroup();
    expect(screen.getByText("⭐ Highest Score")).toBeInTheDocument();
    expect(screen.getByText("⏱️ Shortest Time")).toBeInTheDocument();
    expect(screen.getByText("🎯 Blended")).toBeInTheDocument();
  });

  test("calls setSortType with 'score' when score button is clicked", () => {
    const { setSortType } = renderSortButtonGroup();
    fireEvent.click(screen.getByText("⭐ Highest Score"));
    expect(setSortType).toHaveBeenCalledWith("score");
  });

  test("calls setSortType with 'time' when time button is clicked", () => {
    const { setSortType } = renderSortButtonGroup();
    fireEvent.click(screen.getByText("⏱️ Shortest Time"));
    expect(setSortType).toHaveBeenCalledWith("time");
  });

  test("calls setSortType with 'blended' when blended button is clicked", () => {
    const { setSortType } = renderSortButtonGroup();
    fireEvent.click(screen.getByText("🎯 Blended"));
    expect(setSortType).toHaveBeenCalledWith("blended");
  });

  test("renders score button as contained when sortType is score", () => {
    renderSortButtonGroup({ sortType: "score" });
    const scoreButton = screen.getByText("⭐ Highest Score");
    expect(scoreButton.closest("button")).toHaveClass("MuiButton-contained");
  });

  test("renders time button as contained when sortType is time", () => {
    renderSortButtonGroup({ sortType: "time" });
    const timeButton = screen.getByText("⏱️ Shortest Time");
    expect(timeButton.closest("button")).toHaveClass("MuiButton-contained");
  });

  test("renders blended button as contained when sortType is blended", () => {
    renderSortButtonGroup({ sortType: "blended" });
    const blendedButton = screen.getByText("🎯 Blended");
    expect(blendedButton.closest("button")).toHaveClass("MuiButton-contained");
  });

  test("renders other buttons as outlined when a specific sort is active", () => {
    renderSortButtonGroup({ sortType: "score" });
    const timeButton = screen.getByText("⏱️ Shortest Time");
    const blendedButton = screen.getByText("🎯 Blended");
    expect(timeButton.closest("button")).toHaveClass("MuiButton-outlined");
    expect(blendedButton.closest("button")).toHaveClass("MuiButton-outlined");
  });
});
