import { Typography, List, ListItem, ListItemText } from "@mui/material"
import { useGetMyBacklog } from "./hooks/useGetMyBacklog"

export function MyBacklog() {
    const { data, isSuccess } = useGetMyBacklog();
    const games = data?.data?.games ?? []

    return (
        <>
            <Typography variant="h4" sx={{ mt: 2 }}>My Backlog</Typography>

            {!isSuccess ? (
                <Typography>Loading…</Typography>
            ) : games.length === 0 ? (
                <Typography>No games in your backlog.</Typography>
            ) : (
                <List>
                    {games.map(g => (
                        <ListItem key={g.gameId ?? g.title}>
                            <ListItemText primary={g.title} />
                        </ListItem>
                    ))}
                </List>
            )}
        </>
    )
}
