import { createBlendedComparator } from "../src/blended-comparator";
import { BacklogGameRow } from "../src/client";
import { expect, expectTypeOf, test } from "vitest";

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
  const sorted = backlogGames.sort(comparator);
  expect(sorted.map((x) => x.gameId)).toEqual([1, 2, 3]);
});

test("does not error when empty list is passed in", () => {
  const backlogGames: BacklogGameRow[] = [];
  const comparator = createBlendedComparator(backlogGames);
  const sorted = backlogGames.sort(comparator);
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
  const sorted = backlogGames.sort(comparator);
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
  const sorted = backlogGames.sort(comparator);
  expect(sorted.map((x) => x.gameId)).toEqual([1, 3, 2]);
});
