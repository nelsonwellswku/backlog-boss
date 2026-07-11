import Chip from "@mui/material/Chip";

const MAX_VISIBLE_GENRES = 3;

type GenreChipsProps = {
  genres: string[];
};

export function GenreChips({ genres }: GenreChipsProps) {
  if (genres.length === 0) {
    return null;
  }

  return (
    <>
      {genres.slice(0, MAX_VISIBLE_GENRES).map((genre) => (
        <Chip key={genre} size="small" label={genre} variant="outlined" />
      ))}
      {genres.length > MAX_VISIBLE_GENRES && (
        <Chip
          size="small"
          label={`+${genres.length - MAX_VISIBLE_GENRES}`}
          variant="outlined"
        />
      )}
    </>
  );
}
