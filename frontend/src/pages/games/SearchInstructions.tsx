import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";

export function SearchInstructions() {
  return (
    <Paper
      variant="outlined"
      sx={{ p: 3, borderRadius: 3, bgcolor: "background.paper" }}
    >
      <Typography variant="h6" gutterBottom>
        Search by title
      </Typography>
      <Typography color="text.secondary">
        Results include the game name, review score, and time-to-beat when
        available.
      </Typography>
    </Paper>
  );
}
