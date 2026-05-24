import Alert from "@mui/material/Alert";

type NoResultsAlertProps = {
  submittedQuery: string;
};

export function NoResultsAlert({ submittedQuery }: NoResultsAlertProps) {
  return (
    <Alert severity="info">No games found for "{submittedQuery}".</Alert>
  );
}
