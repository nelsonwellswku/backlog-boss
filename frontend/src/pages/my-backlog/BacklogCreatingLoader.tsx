import { useState, useEffect } from "react";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";

const CREATION_MESSAGES = [
  "Creating your backlog...",
  "Fetching your games from Steam...",
  "Fetching game ratings...",
  "Fetching game times to beat...",
  "Finalizing your backlog...",
];

export function BacklogCreatingLoader() {
  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((prev) => {
        if (prev < CREATION_MESSAGES.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "60vh",
        gap: 3,
      }}
    >
      <CircularProgress size={60} thickness={4} />
      <Typography variant="h5" sx={{ fontWeight: 500 }}>
        {CREATION_MESSAGES[messageIndex]}
      </Typography>
      <Typography variant="body1" color="text.secondary">
        This will only take a moment
      </Typography>
    </Box>
  );
}
