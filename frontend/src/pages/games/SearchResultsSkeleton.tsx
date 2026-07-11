import Box from "@mui/material/Box";
import Divider from "@mui/material/Divider";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Paper from "@mui/material/Paper";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

function GameListItemSkeleton({ isLast }: { isLast: boolean }) {
  return (
    <Box>
      <ListItem
        sx={{ py: 2.5, px: 3 }}
        secondaryAction={
          <Skeleton variant="rounded" width={120} height={32} />
        }
      >
        <ListItemText
          slotProps={{ secondary: { component: "div" } }}
          primary={
            <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
              <Skeleton variant="text" width="40%" height={28} />
            </Stack>
          }
          secondary={
            <Stack
              direction="row"
              spacing={1}
              sx={{ mt: 1.5, flexWrap: "wrap", rowGap: 1 }}
            >
              <Skeleton variant="rounded" width={90} height={28} />
              <Skeleton variant="rounded" width={80} height={28} />
              <Skeleton variant="rounded" width={60} height={24} />
              <Skeleton variant="rounded" width={60} height={24} />
              <Skeleton variant="rounded" width={60} height={24} />
            </Stack>
          }
        />
      </ListItem>
      {!isLast ? <Divider /> : null}
    </Box>
  );
}

export function SearchResultsSkeleton({
  submittedQuery,
}: { submittedQuery: string }) {
  return (
    <Paper variant="outlined" sx={{ borderRadius: 3, bgcolor: "background.paper" }}>
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
        <Typography variant="h6">Searching for &quot;{submittedQuery}&quot;</Typography>
        <Typography variant="body2" color="text.secondary">
          Pulling matching games from the local catalog and IGDB if needed.
        </Typography>
      </Box>
      <List sx={{ py: 0 }}>
        {Array.from({ length: 5 }).map((_, i) => (
          <GameListItemSkeleton key={i} isLast={i === 4} />
        ))}
      </List>
    </Paper>
  );
}
