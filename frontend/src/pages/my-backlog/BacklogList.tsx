import type { BacklogGameRow } from "@bb/client";
import Box from "@mui/material/Box";
import Divider from "@mui/material/Divider";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";

type PropType = {
  games: BacklogGameRow[];
};

export function BacklogList({ games }: PropType) {
  return (
    <Paper elevation={2} sx={{ borderRadius: 2 }}>
      <List sx={{ py: 0 }}>
        {games.map((g, index) => (
          <Box key={g.gameId}>
            <ListItem
              sx={{
                py: 2,
                px: 3,
                "&:hover": {
                  backgroundColor: "action.hover",
                },
              }}
            >
              <ListItemText
                primary={g.title}
                secondary={
                  <Box
                    component="span"
                    sx={{ display: "flex", gap: 2, mt: 0.5 }}
                  >
                    {g.timeToBeat && (
                      <Typography
                        component="span"
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          display: "flex",
                          alignItems: "center",
                          gap: 0.5,
                        }}
                      >
                        ⏱️ {Math.round(g.timeToBeat / 3600)}h
                      </Typography>
                    )}
                    {g.totalRating && (
                      <Typography
                        component="span"
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          display: "flex",
                          alignItems: "center",
                          gap: 0.5,
                        }}
                      >
                        ⭐ {Math.round(g.totalRating)}/100
                      </Typography>
                    )}
                  </Box>
                }
                slotProps={{
                  primary: {
                    variant: "body1",
                    fontWeight: 500,
                  },
                }}
              />
            </ListItem>
            {index < games.length - 1 && <Divider />}
          </Box>
        ))}
      </List>
    </Paper>
  );
}
