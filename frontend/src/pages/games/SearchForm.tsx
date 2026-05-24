import SearchIcon from "@mui/icons-material/Search";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import type { SubmitEventHandler } from "react";

type SearchFormProps = {
  isPending: boolean;
  onQueryChange: (value: string) => void;
  onSearch: SubmitEventHandler<HTMLFormElement>;
  query: string;
};

export function SearchForm({
  isPending,
  onQueryChange,
  onSearch,
  query,
}: SearchFormProps) {
  const isSearchDisabled = query.trim().length === 0 || isPending;

  return (
    <Box component="form" onSubmit={onSearch}>
      <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
        <TextField
          fullWidth
          label="Game name"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
        />
        <Button
          type="submit"
          variant="contained"
          size="large"
          disabled={isSearchDisabled}
          startIcon={
            isPending ? (
              <CircularProgress size={20} color="inherit" />
            ) : (
              <SearchIcon />
            )
          }
          sx={{ minWidth: { md: 180 } }}
        >
          {isPending ? "Searching…" : "Search"}
        </Button>
      </Stack>
    </Box>
  );
}
