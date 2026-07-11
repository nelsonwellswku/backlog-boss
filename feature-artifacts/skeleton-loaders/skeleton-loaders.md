# Skeleton Loaders

## Goal

Replace text-based and spinner loading states with MUI Skeleton pulse animations across three areas: MyBacklog initial load, search results, and backlog refresh.

## Decisions

- **Animation**: `pulse` (MUI default)
- **MyBacklog skeleton**: Fixed 8 rows (6 active + 2 completed) with section headers
- **Search skeleton**: 5 rows, uniform chip widths
- **Refresh indicator**: `LinearProgress` bar below toolbar
- **Code organization**: Dedicated skeleton files as siblings to their parent components

## Step 1: Create `BacklogListSkeleton.tsx`

**New file:** `frontend/src/pages/my-backlog/BacklogListSkeleton.tsx`

Mirrors the exact layout of `BacklogList.tsx` but replaces real game data with Skeleton placeholders.

Structure:
```
Stack spacing={3}
  Paper (Active Backlog section)
    Box header (same gradient styling as BacklogList.tsx:221-258)
      - Skeleton variant="text" width={180} height={32}   // mirrors "Active Backlog" h6
      - Skeleton variant="text" width={140} height={20}   // mirrors "{N} games to work through"
    List
      6x BacklogListItemSkeleton
        ListItem (py: 2, px: 2 - matches BacklogListItem)
          ListItemText
            primary: Skeleton variant="text" width="45%" height={20}    // title
            secondary: Box with flex row
              Skeleton variant="text" width={40} height={16}           // "⏱️ Nh"
              Skeleton variant="text" width={55} height={16}           // "⭐ N/100"
              3x Skeleton variant="rounded" width={60} height={24}     // genre chips
          Box (action buttons area)
            Skeleton variant="rounded" width={110} height={32}         // "Mark complete" button
            Skeleton variant="circular" width={40} height={40}         // delete icon
          Divider (between rows, not on last)

  Paper (Completed Games section - same as BacklogList.tsx:266-315)
    Box header (success-tinted gradient)
      - Skeleton variant="text" width={200} height={32}   // "Completed Games"
      - Skeleton variant="text" width={160} height={20}   // "{N} completed games"
    List
      2x BacklogListItemSkeleton (same structure, no action buttons)
```

## Step 2: Create `SearchResultsSkeleton.tsx`

**New file:** `frontend/src/pages/games/SearchResultsSkeleton.tsx`

Mirrors the layout of `SearchResults.tsx` + `GameListItem.tsx`.

Structure:
```
Paper variant="outlined"
  Box header
    Typography "Searching for {query}"        // real text, already available
    Typography "Pulling matching games..."    // real text
  List
    5x GameListItemSkeleton
      ListItem (py: 2.5, px: 3 - matches GameListItem.tsx:39)
        ListItemText
          primary: Stack (direction row)
            Skeleton variant="text" width="40%" height={28}    // title (h6 size)
          secondary: Stack (direction row, spacing 1, mt: 1.5)
            Skeleton variant="rounded" width={90} height={28}  // rating chip
            Skeleton variant="rounded" width={80} height={28}  // time chip
            3x Skeleton variant="rounded" width={60} height={24} // genre chips (uniform)
        secondaryAction:
          Skeleton variant="rounded" width={120} height={32}   // "Add to backlog" button
      Divider (between rows, not on last)
```

## Step 3: Update `MyBacklog.tsx`

**Modify:** `frontend/src/pages/my-backlog/MyBacklog.tsx`

1. Import `BacklogListSkeleton` (new file)
2. Import `LinearProgress` from `@mui/material/LinearProgress`
3. Replace line 168 (`<Typography>Loading…</Typography>`) with:
   ```tsx
   <BacklogListSkeleton />
   ```
4. Add LinearProgress for refresh state — insert between the toolbar `Box` (line 176-196) and the `BacklogList` (line 197):
   ```tsx
   {isRefreshing && <LinearProgress sx={{ mt: -2, mb: 2 }} />}
   ```

## Step 4: Update `GamesView.tsx`

**Modify:** `frontend/src/pages/games/GamesView.tsx`

1. Import `SearchResultsSkeleton` (new file)
2. Replace lines 120-138 (the `isPending` spinner block) with:
   ```tsx
   {isPending ? (
     <SearchResultsSkeleton submittedQuery={submittedQuery} />
   ) : null}
   ```

## Files Changed Summary

| File | Action | Description |
|---|---|---|
| `frontend/src/pages/my-backlog/BacklogListSkeleton.tsx` | **Create** | 8-row skeleton matching BacklogList layout |
| `frontend/src/pages/games/SearchResultsSkeleton.tsx` | **Create** | 5-row skeleton matching SearchResults layout |
| `frontend/src/pages/my-backlog/MyBacklog.tsx` | **Modify** | Replace "Loading..." text with skeleton, add LinearProgress for refresh |
| `frontend/src/pages/games/GamesView.tsx` | **Modify** | Replace CircularProgress spinner with SearchResultsSkeleton |

## Verification

1. `cd frontend && npm run build` — confirm no TypeScript errors
2. `cd frontend && npm run lint` — confirm no lint errors
3. Manual test: navigate to `/my-backlog` while not logged in (or with slow network) — should see skeleton pulse
4. Manual test: search for a game — should see 5 skeleton rows replace the spinner
5. Manual test: click "Refresh Backlog" — should see LinearProgress bar appear
