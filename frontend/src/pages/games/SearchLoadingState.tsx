import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

type SearchLoadingStateProps = {
  submittedQuery: string;
};

export function SearchLoadingState({ submittedQuery }: SearchLoadingStateProps) {
  return (
    <Paper
      variant="outlined"
      sx={{ p: 3, borderRadius: 3, bgcolor: "background.paper" }}
    >
      <Stack direction="row" spacing={2} sx={{ alignItems: "center" }}>
        <CircularProgress size={32} />
        <Box>
          <Typography variant="h6" gutterBottom>
            Searching for "{submittedQuery}"
          </Typography>
          <Typography color="text.secondary">
            Pulling matching games from the local catalog and IGDB if needed.
          </Typography>
        </Box>
      </Stack>
    </Paper>
  );
}
