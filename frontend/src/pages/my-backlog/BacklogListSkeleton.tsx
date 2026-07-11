import Box from "@mui/material/Box";
import Divider from "@mui/material/Divider";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Paper from "@mui/material/Paper";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";

function BacklogListItemSkeleton({ noActions }: { noActions?: boolean }) {
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
      {!noActions && (
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, ml: 2 }}>
          <Skeleton variant="rounded" width={110} height={32} />
          <Skeleton variant="circular" width={40} height={40} />
        </Box>
      )}
    </ListItem>
  );
}

export function BacklogListSkeleton() {
  return (
    <Stack spacing={3}>
      <Paper elevation={2} sx={{ borderRadius: 2, overflow: "hidden" }}>
        <Box
          sx={{
            px: 3,
            py: 2,
            borderBottom: "1px solid",
            borderColor: "divider",
            background:
              "linear-gradient(180deg, rgba(25,118,210,0.08) 0%, rgba(25,118,210,0.02) 100%)",
          }}
        >
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 2,
              flexWrap: "wrap",
            }}
          >
            <Box>
              <Skeleton variant="text" width={180} height={32} />
              <Skeleton variant="text" width={140} height={20} />
            </Box>
          </Box>
        </Box>
        <List sx={{ py: 0 }}>
          {Array.from({ length: 6 }).map((_, i) => (
            <Box key={i}>
              <BacklogListItemSkeleton />
              {i < 5 && <Divider />}
            </Box>
          ))}
        </List>
      </Paper>

      <Paper
        elevation={1}
        sx={{
          borderRadius: 2,
          overflow: "hidden",
          border: "1px solid",
          borderColor: "success.light",
          backgroundColor: "rgba(76, 175, 80, 0.04)",
        }}
      >
        <Box
          sx={{
            px: 3,
            py: 2,
            borderBottom: "1px solid",
            borderColor: "success.light",
            background:
              "linear-gradient(180deg, rgba(76,175,80,0.12) 0%, rgba(76,175,80,0.04) 100%)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: 2,
            flexWrap: "wrap",
          }}
        >
          <Box>
            <Skeleton variant="text" width={200} height={32} />
            <Skeleton variant="text" width={160} height={20} />
          </Box>
        </Box>
        <List sx={{ py: 0 }}>
          {Array.from({ length: 2 }).map((_, i) => (
            <Box key={i}>
              <BacklogListItemSkeleton noActions />
              {i < 1 && <Divider />}
            </Box>
          ))}
        </List>
      </Paper>
    </Stack>
  );
}
