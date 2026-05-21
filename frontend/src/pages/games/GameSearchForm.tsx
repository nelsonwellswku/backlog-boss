import SearchIcon from "@mui/icons-material/Search";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useForm } from "@tanstack/react-form";

import type { GameSearchRow } from "@bb/client";

type GameSearchFormProps = {
  onSearch: (query: string) => Promise<GameSearchRow[]>;
  isPending: boolean;
  onSubmitSuccess: (results: GameSearchRow[]) => void;
};

export function GameSearchForm({
  onSearch,
  isPending,
  onSubmitSuccess,
}: GameSearchFormProps) {
  const form = useForm({
    defaultValues: { query: "" },
    onSubmit: async ({ value }) => {
      const results = await onSearch(value.query);
      onSubmitSuccess(results);
    },
  });

  return (
    <Paper
      elevation={3}
      sx={{
        p: { xs: 3, md: 4 },
        mb: 4,
        borderRadius: 3,
        background:
          "linear-gradient(135deg, rgba(102,126,234,0.15) 0%, rgba(118,75,162,0.12) 100%)",
      }}
    >
      <Stack spacing={3}>
        <Box>
          <Typography
            variant="h3"
            component="h1"
            gutterBottom
            sx={{ fontWeight: "bold" }}
          >
            Discover Games
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Search the Backlog Boss catalog and, when needed, pull fresh Steam
            game data from IGDB.
          </Typography>
        </Box>

        <Box
          component="form"
          onSubmit={(e) => {
            e.preventDefault();
            e.stopPropagation();
            void form.handleSubmit();
          }}
        >
          <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
            <form.Field
              name="query"
              validators={{
                onChange: ({ value }) =>
                  value.trim().length === 0 ? "Required" : undefined,
              }}
            >
              {(field) => (
                <TextField
                  fullWidth
                  label="Game name"
                  value={field.state.value}
                  onChange={(e) => field.handleChange(e.target.value)}
                  onBlur={field.handleBlur}
                />
              )}
            </form.Field>
            <form.Subscribe
              selector={(state) =>
                [state.values.query, state.isSubmitting] as const
              }
            >
              {([query, isSubmitting]) => {
                const isLoading = isSubmitting || isPending;
                const isSearchDisabled = query.trim().length === 0 || isLoading;
                return (
                  <Button
                    type="submit"
                    variant="contained"
                    size="large"
                    disabled={isSearchDisabled}
                    startIcon={
                      isLoading ? (
                        <CircularProgress size={20} color="inherit" />
                      ) : (
                        <SearchIcon />
                      )
                    }
                    sx={{ minWidth: { md: 180 } }}
                  >
                    {isLoading ? "Searching…" : "Search"}
                  </Button>
                );
              }}
            </form.Subscribe>
          </Stack>
        </Box>
      </Stack>
    </Paper>
  );
}
