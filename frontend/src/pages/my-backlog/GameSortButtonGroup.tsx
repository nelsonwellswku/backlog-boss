import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import ButtonGroup from "@mui/material/ButtonGroup";
import Typography from "@mui/material/Typography";
import type { SortType } from "@bb/pages/my-backlog/SortType";

type PropType = {
  sortType: SortType;
  setSortType: React.Dispatch<React.SetStateAction<SortType>>;
};

export function GameSortButtonGroup({ sortType, setSortType }: PropType) {
  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        mb: 3,
      }}
    >
      <Typography variant="h4" sx={{ fontWeight: "bold" }}>
        My Backlog
      </Typography>
      <ButtonGroup variant="outlined" size="small">
        <Button
          onClick={() => setSortType(sortType === "score" ? null : "score")}
          variant={sortType === "score" ? "contained" : "outlined"}
        >
          ⭐ Highest Score
        </Button>
        <Button
          onClick={() => setSortType(sortType === "time" ? null : "time")}
          variant={sortType === "time" ? "contained" : "outlined"}
        >
          ⏱️ Shortest Time
        </Button>
        <Button
          onClick={() => setSortType(sortType === "blended" ? null : "blended")}
          variant={sortType === "blended" ? "contained" : "outlined"}
        >
          🎯 Blended
        </Button>
      </ButtonGroup>
    </Box>
  );
}
