# Plan: Tabbed My Backlog Page

## Goal

Reorganize the My Backlog page into two tabs — Active Backlog and Completed Games — with per-tab data fetching.

## Decisions (from grill session)

| Decision | Choice |
|----------|--------|
| Backend API | Add `?status=active\|completed` query param to existing endpoint |
| Tab component | MUI Tabs |
| Data fetching | Separate query keys per tab, `staleTime: 0`, `keepPreviousData: true` |
| Completing a game | Local state cue via `completedInSessionIds`, no refetch; game disappears from Active on next tab switch |
| Refresh button | `invalidateQueries({ queryKey: ["myBacklog"] })` — invalidates both tabs |
| Loading states | Skeleton on first load, LinearProgress on subsequent fetches |
| Sort control | Inside Active tab only |
| Tab labels | Plain text, no counts |
| Empty tab messages | "No games in your backlog yet." / "No completed games yet." |
| No-backlog state | Creation prompt only — no tabs, no refresh button |

---

## Step 1: Backend — Add `status` query parameter

**File: `backend/app/features/user/get_my_backlog_handler.py`**

- Add `status: str | None = None` parameter to `handle()` method
- After fetching the backlog, filter `backlog.backlog_games` by status:
  - `status="active"` → only games where `completed_on IS NULL`
  - `status="completed"` → only games where `completed_on IS NOT NULL`
  - `None` → all non-removed games (backward compatible)
- Apply the filter before building `backlog_game_rows`

**File: `backend/app/features/user/user_router.py`**

- Import `Query` from FastAPI
- Add `status: str | None = Query(None)` parameter to the `get_my_backlog` endpoint function, pass it to `handler.handle(status=status)`

## Step 2: Regenerate OpenAPI + client

```bash
cd backend && uv run python export_openapi.py
cd ../frontend && npm run genclient
```

This updates `frontend/src/client/types.gen.ts` to include `query?: { status?: "active" | "completed" }` in `UserGetMyBacklogData`.

## Step 3: New hook — `useGetMyBacklogTab`

**New file: `frontend/src/hooks/useGetMyBacklogTab.ts`**

```ts
export function useGetMyBacklogTab(status: "active" | "completed") {
  return useQuery({
    queryKey: ["myBacklog", status],
    queryFn: () => userGetMyBacklog({ query: { status } }),
    retry: false,
    keepPreviousData: true,
  });
}
```

- `queryKey: ["myBacklog", status]` — separate cache per tab
- `keepPreviousData: true` — shows stale content while fetching
- The existing `useGetMyBacklog` (no param) stays for the initial 404 check

## Step 4: Update `useRefreshMyBacklog`

**File: `frontend/src/hooks/useRefreshMyBacklog.ts`**

- Already calls `queryClient.invalidateQueries({ queryKey: ["myBacklog"] })`
- This invalidates both `["myBacklog", "active"]` and `["myBacklog", "completed"]` via prefix match
- No changes needed

## Step 5: Update `useUpdateBacklogGame`

**File: `frontend/src/hooks/useUpdateBacklogGame.ts`**

- Already calls `queryClient.invalidateQueries({ queryKey: ["myBacklog"] })`
- This invalidates both tab caches after a mutation
- No changes needed

## Step 6: Refactor `MyBacklog` component

**File: `frontend/src/pages/my-backlog/MyBacklog.tsx`**

Major restructuring:

1. **Keep the initial 404 check**: Use the existing `useGetMyBacklog()` (no status param) to detect if a backlog exists. If 404, show `CreateBacklogPrompt` — no tabs.

2. **Add tab state**: `const [activeTab, setActiveTab] = useState<"active" | "completed">("active")`

3. **Fetch per tab**: Use `useGetMyBacklogTab(activeTab)` for the visible tab. But also keep the other tab's query warm — when `isSuccess` is true (backlog exists), mount both tab queries so switching is instant:
   ```ts
   const activeTabQuery = useGetMyBacklogTab("active");
   const completedTabQuery = useGetMyBacklogTab("completed");
   // Only use the active tab's data for display
   const currentQuery = activeTab === "active" ? activeTabQuery : completedTabQuery;
   ```

4. **Sorting**: Only applies to active tab. Sort `activeTabQuery.data?.games` with the existing sort logic.

5. **`completedInSessionIds`**: Track games toggled complete in this session. On the Active tab, games in this set stay visible with a completed cue. On the Completed tab, they appear naturally (server has `completed_on` set).

6. **Loading states**: 
   - First load of a tab (`currentQuery.data === undefined && currentQuery.isPreviousData === false`): show `BacklogListSkeleton`
   - Subsequent fetches (`currentQuery.isPreviousData === true`): show `LinearProgress` over existing content

7. **Refresh button**: Calls `refreshBacklog()` which invalidates both queries. Shows "Refreshing..." while `isRefreshing` is true.

8. **Remove jump links**: Delete `scrollToCompletedGames` and `scrollToTopOfBacklog` from the component.

9. **Render structure**:
   ```
   <Box>
     <Typography variant="h4">My Backlog</Typography>
     <Button onClick={handleRefreshBacklog}>Refresh Backlog</Button>
     <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)}>
       <Tab label="Active Backlog" value="active" />
       <Tab label="Completed Games" value="completed" />
     </Tabs>
     {activeTab === "active" && <GameSortButtonGroup />}
     {isRefreshing && <LinearProgress />}
     {activeTab === "active" 
       ? <BacklogTabContent games={sortedActiveGames} ... />
       : <BacklogTabContent games={completedGames} ... />
     }
     <RemoveGameDialog ... />
   </Box>
   ```

## Step 7: Create `BacklogTabContent` component

**New file: `frontend/src/pages/my-backlog/BacklogTabContent.tsx`**

- Replaces the two-section `BacklogList` for tab content
- Renders a single `<Paper>` with a `<List>` of `BacklogListItem`s
- Props: `games`, `onToggleCompleted`, `onRemoveGame`, `updatingBacklogGameId`, `emptyMessage`
- When `games.length === 0`, shows the empty message centered

## Step 8: Delete `BacklogList`

**File: `frontend/src/pages/my-backlog/BacklogList.tsx`**

- Delete entirely — replaced by `BacklogTabContent`
- The old component's two-section layout, jump scrolls, and game counts are no longer needed

## Step 9: Handle `completedInSessionIds` with tab queries

The merge logic is simpler with separate query keys:

- **Active tab**: Server returns only non-completed games. `completedInSessionIds` games are NOT in the server results. After a tab switch, they disappear from Active (server filtered them out).
- **Completed tab**: Server returns only completed games. Games in `completedInSessionIds` ARE in the server results (server has `completed_on` set). No special merge needed.

The `completedInSessionIds` is used in `BacklogTabContent` to determine `isCompleted` for the visual cue:
```ts
const isCompleted = game.completedOn || completedInSessionSet.has(game.backlogGameId);
```

## Step 10: Tests

- Backend: Add tests for `?status=active` and `?status=completed` filtering
- Frontend: Verify tab switching, sort behavior, completion toggle, refresh button, empty states

---

## File Change Summary

| File | Action |
|------|--------|
| `backend/app/features/user/get_my_backlog_handler.py` | Modify — add `status` param + filter |
| `backend/app/features/user/user_router.py` | Modify — add `status` query param to endpoint |
| `frontend/src/hooks/useGetMyBacklogTab.ts` | **New** — tab-specific query hook |
| `frontend/src/pages/my-backlog/MyBacklog.tsx` | Modify — tabs, per-tab fetch, remove jump links |
| `frontend/src/pages/my-backlog/BacklogTabContent.tsx` | **New** — single-tab game list |
| `frontend/src/pages/my-backlog/BacklogList.tsx` | **Delete** — replaced by BacklogTabContent |
| `frontend/src/client/` | Regenerated via codegen |
