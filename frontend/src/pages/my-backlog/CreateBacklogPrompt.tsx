import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";

interface CreateBacklogPromptProps {
  onCreateBacklog: () => void;
}

export function CreateBacklogPrompt({
  onCreateBacklog,
}: CreateBacklogPromptProps) {
  return (
    <Box sx={{ textAlign: "center", mt: 4 }}>
      <Typography variant="h6" gutterBottom>
        You don't currently have a backlog.
      </Typography>
      <Typography color="text.secondary" paragraph>
        Would you like to create one?
      </Typography>
      <Button variant="contained" onClick={onCreateBacklog}>
        Create My Backlog
      </Button>
    </Box>
  );
}
