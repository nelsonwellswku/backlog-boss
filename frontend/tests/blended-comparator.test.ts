import { createBlendedComparator } from "@bb/pages/my-backlog/blended-comparator";
import type { BacklogGameRow } from "@bb/client";
import { expect, test } from "vitest";

test("blended comparator correctly sorts games with weight given to time", () => {
  const backlogGames: BacklogGameRow[] = [
    {
      gameId: 2,
      title: "Legend of Zelda",
      timeToBeat: 1000,
      totalRating: 98,
    },
    {
      gameId: 1,
      title: "Mario Bros.",
      timeToBeat: 600,
      totalRating: 95,
    },
    {
      gameId: 3,
      title: "Metroid",
      timeToBeat: 2000,
      totalRating: 99,
    },
  ];

  const comparator = createBlendedComparator(backlogGames);
  const sorted = backlogGames.toSorted(comparator);
  expect(sorted.map((x) => x.gameId)).toEqual([1, 2, 3]);
});

test("does not error when empty list is passed in", () => {
  const backlogGames: BacklogGameRow[] = [];
  const comparator = createBlendedComparator(backlogGames);
  const sorted = backlogGames.toSorted(comparator);
  expect(sorted).toEqual([]);
});

test("correctly sorts games with no time to beat to the bottom", () => {
  const backlogGames: BacklogGameRow[] = [
    {
      gameId: 1,
      title: "Game One",
      timeToBeat: 500,
      totalRating: 50,
    },
    {
      gameId: 2,
      title: "Game Two",
      timeToBeat: null,
      totalRating: 100,
    },
    {
      gameId: 3,
      title: "Game Three",
      timeToBeat: 1200,
      totalRating: 50,
    },
  ];

  const comparator = createBlendedComparator(backlogGames);
  const sorted = backlogGames.toSorted(comparator);
  expect(sorted.map((x) => x.gameId)).toEqual([1, 3, 2]);
});

test("correctly sorts games with no rating to the bottom", () => {
  const backlogGames: BacklogGameRow[] = [
    {
      gameId: 1,
      title: "Game One",
      timeToBeat: 500,
      totalRating: 50,
    },
    {
      gameId: 2,
      title: "Game Two",
      timeToBeat: 500,
      totalRating: null,
    },
    {
      gameId: 3,
      title: "Game Three",
      timeToBeat: 500,
      totalRating: 50,
    },
  ];

  const comparator = createBlendedComparator(backlogGames);
  const sorted = backlogGames.toSorted(comparator);
  expect(sorted.map((x) => x.gameId)).toEqual([1, 3, 2]);
});

test("correctly sorts games with both null time and null rating to the bottom", () => {
  const backlogGames: BacklogGameRow[] = [
    {
      gameId: 1,
      title: "Game One",
      timeToBeat: 500,
      totalRating: 50,
    },
    {
      gameId: 2,
      title: "Game Two",
      timeToBeat: null,
      totalRating: null,
    },
    {
      gameId: 3,
      title: "Game Three",
      timeToBeat: 600,
      totalRating: 60,
    },
  ];

  const comparator = createBlendedComparator(backlogGames);
  const sorted = backlogGames.toSorted(comparator);
  expect(sorted.map((x) => x.gameId)).toEqual([1, 3, 2]);
});

test("correctly sorts multiple games with null time to beat to the bottom", () => {
  const backlogGames: BacklogGameRow[] = [
    {
      gameId: 1,
      title: "Game One",
      timeToBeat: null,
      totalRating: 80,
    },
    {
      gameId: 2,
      title: "Game Two",
      timeToBeat: 500,
      totalRating: 50,
    },
    {
      gameId: 3,
      title: "Game Three",
      timeToBeat: null,
      totalRating: 90,
    },
  ];

  const comparator = createBlendedComparator(backlogGames);
  const sorted = backlogGames.toSorted(comparator);
  // Game 2 should be first (has time), then the null-time games at the bottom
  expect(sorted[0].gameId).toEqual(2);
  expect([1, 3]).toContain(sorted[1].gameId);
  expect([1, 3]).toContain(sorted[2].gameId);
});

test("handles list with single game", () => {
  const backlogGames: BacklogGameRow[] = [
    {
      gameId: 1,
      title: "Only Game",
      timeToBeat: 500,
      totalRating: 80,
    },
  ];

  const comparator = createBlendedComparator(backlogGames);
  const sorted = backlogGames.toSorted(comparator);
  expect(sorted.map((x) => x.gameId)).toEqual([1]);
});

test("handles all games with null time to beat", () => {
  const backlogGames: BacklogGameRow[] = [
    {
      gameId: 1,
      title: "Game One",
      timeToBeat: null,
      totalRating: 50,
    },
    {
      gameId: 2,
      title: "Game Two",
      timeToBeat: null,
      totalRating: 80,
    },
    {
      gameId: 3,
      title: "Game Three",
      timeToBeat: null,
      totalRating: 60,
    },
  ];

  const comparator = createBlendedComparator(backlogGames);
  const sorted = backlogGames.toSorted(comparator);
  // Should sort by rating when all times are null
  expect(sorted.map((x) => x.gameId)).toEqual([2, 3, 1]);
});

test("handles all games with null rating", () => {
  const backlogGames: BacklogGameRow[] = [
    {
      gameId: 1,
      title: "Game One",
      timeToBeat: 1000,
      totalRating: null,
    },
    {
      gameId: 2,
      title: "Game Two",
      timeToBeat: 500,
      totalRating: null,
    },
    {
      gameId: 3,
      title: "Game Three",
      timeToBeat: 2000,
      totalRating: null,
    },
  ];

  const comparator = createBlendedComparator(backlogGames);
  const sorted = backlogGames.toSorted(comparator);
  // Should sort by time when all ratings are null (shorter time first)
  expect(sorted.map((x) => x.gameId)).toEqual([2, 1, 3]);
});

test("handles games with identical scores and times", () => {
  const backlogGames: BacklogGameRow[] = [
    {
      gameId: 1,
      title: "Game One",
      timeToBeat: 500,
      totalRating: 80,
    },
    {
      gameId: 2,
      title: "Game Two",
      timeToBeat: 500,
      totalRating: 80,
    },
    {
      gameId: 3,
      title: "Game Three",
      timeToBeat: 500,
      totalRating: 80,
    },
  ];

  const comparator = createBlendedComparator(backlogGames);
  const sorted = backlogGames.toSorted(comparator);
  // All games have same score, so order doesn't matter but should not error
  expect(sorted).toHaveLength(3);
  expect(sorted.map((x) => x.gameId).toSorted()).toEqual([1, 2, 3]);
});

test("handles mix of null time and null rating across different games", () => {
  const backlogGames: BacklogGameRow[] = [
    {
      gameId: 1,
      title: "Game One",
      timeToBeat: null,
      totalRating: 90,
    },
    {
      gameId: 2,
      title: "Game Two",
      timeToBeat: 500,
      totalRating: null,
    },
    {
      gameId: 3,
      title: "Game Three",
      timeToBeat: 600,
      totalRating: 80,
    },
  ];

  const comparator = createBlendedComparator(backlogGames);
  const sorted = backlogGames.toSorted(comparator);
  // TODO: not sure that this is actually the order I'd prefer, but
  // it is good enough for now
  expect(sorted.map((x) => x.gameId)).toEqual([2, 3, 1]);
});

test("handles extreme values without errors", () => {
  const backlogGames: BacklogGameRow[] = [
    {
      gameId: 1,
      title: "Very Long Game",
      timeToBeat: 100000,
      totalRating: 100,
    },
    {
      gameId: 2,
      title: "Very Short Game",
      timeToBeat: 1,
      totalRating: 50,
    },
    {
      gameId: 3,
      title: "Average Game",
      timeToBeat: 500,
      totalRating: 50,
    },
  ];

  const comparator = createBlendedComparator(backlogGames);
  const sorted = backlogGames.toSorted(comparator);
  // Should not throw and should return all games
  expect(sorted).toHaveLength(3);
  // Short time is heavily weighted, so game 2 should be first despite low rating
  expect(sorted[0].gameId).toEqual(2);
});
