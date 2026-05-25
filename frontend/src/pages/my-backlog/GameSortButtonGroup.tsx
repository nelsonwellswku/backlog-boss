import Button from "@mui/material/Button";
import ButtonGroup from "@mui/material/ButtonGroup";
import type { SortType } from "@bb/pages/my-backlog/SortType";

type PropType = {
  sortType: SortType;
  setSortType: React.Dispatch<React.SetStateAction<SortType>>;
};

export function GameSortButtonGroup({ sortType, setSortType }: PropType) {
  return (
    <ButtonGroup variant="outlined" size="small">
      <Button
        onClick={() => setSortType("score")}
        variant={sortType === "score" ? "contained" : "outlined"}
      >
        ⭐ Highest Score
      </Button>
      <Button
        onClick={() => setSortType("time")}
        variant={sortType === "time" ? "contained" : "outlined"}
      >
        ⏱️ Shortest Time
      </Button>
      <Button
        onClick={() => setSortType("blended")}
        variant={sortType === "blended" ? "contained" : "outlined"}
      >
        🎯 Blended
      </Button>
    </ButtonGroup>
  );
}
