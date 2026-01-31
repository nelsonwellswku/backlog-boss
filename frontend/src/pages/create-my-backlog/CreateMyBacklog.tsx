import { useEffect, useState } from "react";
import { useCreateMyBacklog } from "@bb/hooks/useCreateMyBacklog";
import { useNavigate } from "react-router";
import { Box, CircularProgress, Typography } from "@mui/material";

const MESSAGES = [
  "Creating your backlog...",
  "Fetching your games from Steam...",
  "Fetching game ratings...",
  "Fetching game times to beat...",
  "Finalizing your backlog...",
];

export function CreateMyBacklog() {
  const navigate = useNavigate();
  const { isSuccess, mutate } = useCreateMyBacklog();
  const [messageIndex, setMessageIndex] = useState(0);

  // Trigger the mutation on mount - users are redirected here after login if they don't have a backlog
  useEffect(() => {
    mutate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Cycle through messages every 2 seconds until the last one
  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((prev) => {
        if (prev < MESSAGES.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  // Redirect when successful
  useEffect(() => {
    if (isSuccess) {
      const timer = setTimeout(() => {
        navigate("/my-backlog");
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [isSuccess, navigate]);

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
        {MESSAGES[messageIndex]}
      </Typography>
      <Typography variant="body1" color="text.secondary">
        This will only take a moment
      </Typography>
    </Box>
  );
}
