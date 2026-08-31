import Box from "@mui/material/Box";
import Divider from "@mui/material/Divider";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Paper from "@mui/material/Paper";
import Skeleton from "@mui/material/Skeleton";

function BacklogListItemSkeleton() {
  return (
    <ListItem sx={{ py: 2, px: 2 }}>
      <ListItemText
        primary={<Skeleton variant="text" width="45%" height={20} />}
        secondary={
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mt: 0.75 }}>
            <Skeleton variant="text" width={40} height={16} />
            <Skeleton variant="text" width={55} height={16} />
            <Skeleton variant="rounded" width={60} height={24} />
            <Skeleton variant="rounded" width={60} height={24} />
            <Skeleton variant="rounded" width={60} height={24} />
          </Box>
        }
        slotProps={{ secondary: { component: "div" } }}
      />
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, ml: 2 }}>
        <Skeleton variant="rounded" width={110} height={32} />
        <Skeleton variant="circular" width={40} height={40} />
      </Box>
    </ListItem>
  );
}

export function BacklogListSkeleton() {
  return (
    <Paper elevation={2} sx={{ borderRadius: 2, overflow: "hidden" }}>
      <List sx={{ py: 0 }}>
        {Array.from({ length: 15 }).map((_, i) => (
          <Box key={i}>
            <BacklogListItemSkeleton />
            {i < 14 && <Divider />}
          </Box>
        ))}
      </List>
    </Paper>
  );
}
