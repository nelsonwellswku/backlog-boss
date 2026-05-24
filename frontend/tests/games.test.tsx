import { render, screen, fireEvent } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router";

const mockMutate = vi.fn();
const mockAddMutate = vi.fn();

const mockUseSearchGames = vi.hoisted(() => vi.fn());
const mockUseCurrentUser = vi.hoisted(() => vi.fn());
const mockUseGetMyBacklog = vi.hoisted(() => vi.fn());
const mockUseAddBacklogGame = vi.hoisted(() => vi.fn());

vi.mock("@bb/hooks/useSearchGames", () => ({
  useSearchGames: mockUseSearchGames,
}));
vi.mock("@bb/hooks/useCurrentUser", () => ({
  useCurrentUser: mockUseCurrentUser,
}));
vi.mock("@bb/hooks/useGetMyBacklog", () => ({
  useGetMyBacklog: mockUseGetMyBacklog,
}));
vi.mock("@bb/hooks/useAddBacklogGame", () => ({
  useAddBacklogGame: mockUseAddBacklogGame,
}));

const { Games } = await import("../src/pages/games/Games");

function setupDefaultMocks() {
  mockUseSearchGames.mockReturnValue({
    data: undefined,
    isError: false,
    isPending: false,
    mutate: mockMutate,
  });
  mockUseCurrentUser.mockReturnValue({ data: undefined });
  mockUseGetMyBacklog.mockReturnValue({
    data: undefined,
    isPending: false,
  });
  mockUseAddBacklogGame.mockReturnValue({
    mutate: mockAddMutate,
    isPending: false,
    variables: undefined,
  });
}

function renderGames() {
  return render(
    <MemoryRouter>
      <Games />
    </MemoryRouter>,
  );
}

function renderGamesStatic() {
  return renderToStaticMarkup(
    <MemoryRouter>
      <Games />
    </MemoryRouter>,
  );
}

describe("Games", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaultMocks();
  });

  test("renders the search page shell with header and hint", () => {
    const markup = renderGamesStatic();
    expect(markup).toContain("Discover Games");
    expect(markup).toContain("Search by title");
  });

  test("renders error alert when search mutation errors", () => {
    mockUseSearchGames.mockReturnValue({
      data: undefined,
      isError: true,
      isPending: false,
      mutate: mockMutate,
    });

    const markup = renderGamesStatic();
    expect(markup).toContain(
      "We couldn&#x27;t search for games right now. Please try again.",
    );
  });

  test("renders loading spinner when search mutation is pending", () => {
    mockUseSearchGames.mockReturnValue({
      data: undefined,
      isError: false,
      isPending: true,
      mutate: mockMutate,
    });

    const markup = renderGamesStatic();
    expect(markup).toContain("MuiCircularProgress");
    expect(markup).not.toContain("Search by title");
  });

  test("renders backlog creation prompt when logged in without backlog", () => {
    mockUseCurrentUser.mockReturnValue({
      data: { data: { steamId: "12345" } },
    });
    mockUseGetMyBacklog.mockReturnValue({
      data: undefined,
      isPending: false,
    });

    const markup = renderGamesStatic();
    expect(markup).toContain("Create your backlog");
  });

  test("does not show backlog alert while backlog is loading", () => {
    mockUseCurrentUser.mockReturnValue({
      data: { data: { steamId: "12345" } },
    });
    mockUseGetMyBacklog.mockReturnValue({
      data: undefined,
      isPending: true,
    });

    const markup = renderGamesStatic();
    expect(markup).not.toContain("Create your backlog");
  });

  test("does not show backlog alert when user is not logged in", () => {
    const markup = renderGamesStatic();
    expect(markup).not.toContain("Create your backlog");
  });

  test("computes backlogGameIds from backlog data", () => {
    mockUseCurrentUser.mockReturnValue({
      data: { data: { steamId: "12345" } },
    });
    mockUseGetMyBacklog.mockReturnValue({
      data: { data: { games: [{ gameId: 1, title: "Hades" }] } },
      isPending: false,
    });

    const markup = renderGamesStatic();
    // has backlog, so no "Create your backlog" prompt
    expect(markup).not.toContain("Create your backlog");
  });

  test("calls searchGames when form is submitted", () => {
    const mutate = vi.fn();
    mockUseSearchGames.mockReturnValue({
      data: undefined,
      isError: false,
      isPending: false,
      mutate,
    });

    renderGames();

    fireEvent.change(screen.getByLabelText("Game name"), {
      target: { value: "Hades" },
    });
    fireEvent.submit(
      screen.getByRole("button", { name: /search/i }).closest("form")!,
    );

    expect(mutate).toHaveBeenCalledWith({ query: "Hades" });
  });

  test("calls addBacklogGame when add to backlog button is clicked", () => {
    const mutate = vi.fn();
    // Search mutation already has data so results appear after form submit
    mockUseSearchGames.mockReturnValue({
      data: {
        data: {
          games: [
            {
              gameId: 1,
              title: "Hades",
              totalRating: 93,
              timeToBeat: 36000,
            },
          ],
        },
      },
      isError: false,
      isPending: false,
      mutate,
    });
    mockUseCurrentUser.mockReturnValue({
      data: { data: { steamId: "12345" } },
    });
    mockUseGetMyBacklog.mockReturnValue({
      data: { data: { games: [] } },
      isPending: false,
    });

    renderGames();

    fireEvent.change(screen.getByLabelText("Game name"), {
      target: { value: "Hades" },
    });
    fireEvent.submit(
      screen.getByRole("button", { name: /search/i }).closest("form")!,
    );

    // After submit, hasSearched=true and results are available
    fireEvent.click(
      screen.getByRole("button", { name: /add to backlog/i }),
    );

    expect(mockAddMutate).toHaveBeenCalledWith(
      { gameId: 1 },
      expect.any(Object),
    );
  });
});
