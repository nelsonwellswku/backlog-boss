import type { BacklogGameRow } from "./client";

export function createBlendedComparator(rawGames: BacklogGameRow[]) {
  // Normalize scores and times to 0-1 range
  const scores = rawGames.map((g) => g.totalRating ?? 0);
  const times = rawGames
    .map((g) => g.timeToBeat ?? Infinity)
    .filter((t) => t !== Infinity);

  const minScore = Math.min(...scores);
  const maxScore = Math.max(...scores);
  const minTime = Math.min(...times);
  const maxTime = Math.max(...times);

  const scoreRange = maxScore - minScore || 1;
  const timeRange = maxTime - minTime || 1;

  // Normalize: higher score is better, shorter time is better
  const normalizeScore = (score: number | null) =>
    score ? (score - minScore) / scoreRange : 0;
  const normalizeTime = (time: number | null) =>
    time ? (maxTime - time) / timeRange : 0;

  return (a: BacklogGameRow, b: BacklogGameRow) => {
    // weight is 3 because that gave the blended results I was looking for
    const timeWeight = 3;
    const scoreA =
      normalizeScore(a.totalRating) + normalizeTime(a.timeToBeat) * timeWeight;
    const scoreB =
      normalizeScore(b.totalRating) + normalizeTime(b.timeToBeat) * timeWeight;
    return scoreB - scoreA;
  };
}
