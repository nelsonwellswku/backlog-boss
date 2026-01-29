import { createBlendedComparator } from "../src/blended-comparator";
import { BacklogGameRow } from "../src/client";
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
  const sorted = backlogGames.sort(comparator);
  expect(sorted.map((x) => x.gameId)).toEqual([1, 2, 3]);
});
