import { render, screen } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter, Route, Routes } from "react-router";

const mockUseCurrentUser = vi.hoisted(() => vi.fn());

vi.mock("@bb/hooks/useCurrentUser", () => ({
  useCurrentUser: mockUseCurrentUser,
}));

const { ProtectedRoute } = await import("../src/layouts/ProtectedRoute");

function renderProtectedRouteStatic(initialEntry = "/my-backlog") {
  return renderToStaticMarkup(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route element={<ProtectedRoute />}>
          <Route path="my-backlog" element={<div>Protected Content</div>} />
        </Route>
        <Route path="/" element={<div>Home Page</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

function renderProtectedRoute(initialEntry = "/my-backlog") {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route element={<ProtectedRoute />}>
          <Route path="my-backlog" element={<div>Protected Content</div>} />
        </Route>
        <Route path="/" element={<div>Home Page</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ProtectedRoute", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("renders spinner while auth is loading", () => {
    mockUseCurrentUser.mockReturnValue({
      data: undefined,
      isSuccess: false,
    });

    const markup = renderProtectedRouteStatic();
    expect(markup).toContain("MuiCircularProgress");
    expect(markup).not.toContain("Protected Content");
    expect(markup).not.toContain("Home Page");
  });

  test("renders child route when user is authenticated", () => {
    mockUseCurrentUser.mockReturnValue({
      data: { data: { steamId: "12345" } },
      isSuccess: true,
    });

    const markup = renderProtectedRouteStatic();
    expect(markup).toContain("Protected Content");
    expect(markup).not.toContain("MuiCircularProgress");
  });

  test("redirects to home when user is not authenticated", () => {
    mockUseCurrentUser.mockReturnValue({
      data: { data: null },
      isSuccess: true,
    });

    renderProtectedRoute();
    expect(screen.getByText("Home Page")).toBeInTheDocument();
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
  });

  test("redirects to home when user query returns no data", () => {
    mockUseCurrentUser.mockReturnValue({
      data: undefined,
      isSuccess: true,
    });

    renderProtectedRoute();
    expect(screen.getByText("Home Page")).toBeInTheDocument();
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
  });
});
