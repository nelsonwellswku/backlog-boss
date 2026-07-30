# Protected My Backlog Route — Technical Implementation Plan

## Goal

Redirect unauthenticated users away from `/my-backlog` to the home page, using a reusable layout route guard that checks auth state before rendering protected content.

## Current State

- `/my-backlog` is rendered unconditionally at `frontend/src/main.tsx:20` — no auth check exists.
- Auth is checked ad-hoc via `useCurrentUser()` (`frontend/src/hooks/useCurrentUser.ts:4`) in each component independently. No React context, no auth provider, no route guards.
- When an unauthenticated user visits `/my-backlog`, the page renders an infinite loading skeleton (`frontend/src/pages/my-backlog/MyBacklog.tsx`) because the backend returns 401 for `GET /api/user/get-my-backlog` (protected by `RequiredCurrentUser`), and the `!isSuccess` branch shows `BacklogListSkeleton` indefinitely.
- `useCurrentUser(false)` calls `GET /api/user/me`, which returns `null` when not logged in (no 401 — uses `CurrentUser` optional dependency).
- The `Layout` component already calls `useCurrentUser(false)` and conditionally hides the "My Backlog" nav link (`frontend/src/layouts/Layout.tsx:40-48`), but this is cosmetic only.

## Files to Modify/Create

| File | Action |
|------|--------|
| `frontend/src/layouts/ProtectedRoute.tsx` | Create — layout route component that guards child routes |
| `frontend/src/main.tsx` | Modify — wrap `/my-backlog` in `ProtectedRoute` layout route |

## Step-by-Step Instructions

### Step 1 — Create `ProtectedRoute` component

Create `frontend/src/layouts/ProtectedRoute.tsx`:

```tsx
import { CircularProgress, Container } from "@mui/material";
import { Navigate, Outlet } from "react-router";
import { useCurrentUser } from "@bb/hooks/useCurrentUser";

export function ProtectedRoute() {
  const { data, isSuccess } = useCurrentUser(false);

  if (!isSuccess) {
    return (
      <Container
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: "50vh",
        }}
      >
        <CircularProgress />
      </Container>
    );
  }

  if (!data?.data) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
```

Key details:
- Uses `useCurrentUser(false)` (retry: false) — matches the pattern used in `Layout.tsx:15`, `Home.tsx:22`, and `Games.tsx:24`
- While the auth query is loading (`!isSuccess`): renders a centered MUI `CircularProgress` spinner
- If auth resolved and no user (`!data?.data`): redirects to `/` with `<Navigate to="/" replace />`
- If auth resolved and user exists: renders `<Outlet />` which nests child routes inside the `Layout`
- `replace` on `<Navigate>` ensures the protected route is removed from browser history (back button won't return to it)
- Reusable — any future protected route can be nested under this layout route

### Step 2 — Update route definitions in `main.tsx`

Modify `frontend/src/main.tsx` to nest `/my-backlog` under `ProtectedRoute`:

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router";
import { Layout } from "@bb/layouts/Layout";
import { ProtectedRoute } from "@bb/layouts/ProtectedRoute";
import { Home } from "@bb/pages/home/Home";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Games } from "@bb/pages/games/Games";
import { MyBacklog } from "@bb/pages/my-backlog/MyBacklog";

const queryClient = new QueryClient();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="games" element={<Games />} />
            <Route element={<ProtectedRoute />}>
              <Route path="my-backlog" element={<MyBacklog />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
```

Key details:
- `ProtectedRoute` is a layout route (renders `<Outlet />`), not a wrapper — it sits as a parent `<Route>` with no `path`
- `/my-backlog` becomes a child of `ProtectedRoute`, which is itself a child of `Layout`
- The nesting chain is: `Layout` → `ProtectedRoute` → `MyBacklog`
- When `ProtectedRoute` renders `<Navigate to="/" replace />`, it replaces the current history entry, so the user won't get stuck in a redirect loop
- `ProtectedRoute` reuses the same `useCurrentUser` query instance as `Layout` — React Query deduplicates the request, so there's no extra network call

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Guard type | Layout route with `<Outlet />` | Allows any number of protected routes to be nested; user expects more protected routes in the future |
| Auth check hook | `useCurrentUser(false)` | Same hook used by `Layout`, `Home`, `Games` — retry: false ensures fast failure, React Query deduplicates the call across components |
| Loading state | Centered `CircularProgress` | Communicates "checking auth" without implying content is loading; consistent with MUI design system |
| Redirect target | `/` (home) | Home page already handles unauthenticated users with the Steam login button; consistent with logout redirect behavior |
| Defense-in-depth in MyBacklog | None (guard only) | User prefers single responsibility — protected routes are guarded at the route level, not in every component |
| `replace` on Navigate | Yes | Prevents back-button loops; the protected route is removed from history when redirecting |

## Edge Cases

- **Auth cookie expired mid-session**: `useCurrentUser` will return `isSuccess: true` with `data.data: null`. The guard redirects to `/`. If the user navigates to `/my-backlog` again, the guard re-checks and redirects again — no infinite loop because `replace` removes the history entry.
- **React Query deduplication**: Both `Layout` and `ProtectedRoute` call `useCurrentUser(false)` with the same query key `["currentUser"]`. React Query issues a single network request and shares the result — no performance penalty.
- **Direct URL access**: User types `localhost:5173/my-backlog` in the browser. Guard checks auth → spinner → redirect to `/` if unauthenticated. Works identically to in-app navigation.
- **Back button after redirect**: `replace` prevents the user from pressing back to return to `/my-backlog`. They'd go back to whatever page they were on before.
- **Future protected routes**: Add any new protected route as a child of `<Route element={<ProtectedRoute />}>`. No changes to `ProtectedRoute` needed.
