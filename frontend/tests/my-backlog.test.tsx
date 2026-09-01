import { renderToStaticMarkup } from "react-dom/server";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router";

const mockGetMyBacklog = vi.hoisted(() => vi.fn());
const mockGetMyBacklogTab = vi.hoisted(() => vi.fn());
const mockCreateMyBacklog = vi.hoisted(() => vi.fn());
const mockRefreshMyBacklog = vi.hoisted(() => vi.fn());
const mockUpdateBacklogGame = vi.hoisted(() => vi.fn());
const mockQueryClient = vi.hoisted(() => ({
  invalidateQueries: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("@tanstack/react-query", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@tanstack/react-query")>();
  return {
    ...actual,
    useQueryClient: () => mockQueryClient,
  };
});
vi.mock("@bb/hooks/useGetMyBacklog", () => ({
  useGetMyBacklog: mockGetMyBacklog,
}));
vi.mock("@bb/hooks/useGetMyBacklogTab", () => ({
  useGetMyBacklogTab: mockGetMyBacklogTab,
}));
vi.mock("@bb/hooks/useCreateMyBacklog", () => ({
  useCreateMyBacklog: mockCreateMyBacklog,
}));
vi.mock("@bb/hooks/useRefreshMyBacklog", () => ({
  useRefreshMyBacklog: mockRefreshMyBacklog,
}));
vi.mock("@bb/hooks/useUpdateBacklogGame", () => ({
  useUpdateBacklogGame: mockUpdateBacklogGame,
}));

const { MyBacklog } = await import("../src/pages/my-backlog/MyBacklog");

function setupDefaultMocks() {
  mockGetMyBacklog.mockReturnValue({
    data: undefined,
    isSuccess: false,
    refetch: vi.fn(),
  });
  mockGetMyBacklogTab.mockReturnValue({
    data: undefined,
    isLoading: true,
    isFetching: false,
    isPreviousData: false,
    isPlaceholderData: false,
  });
  mockCreateMyBacklog.mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
  });
  mockRefreshMyBacklog.mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
  });
  mockUpdateBacklogGame.mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
    variables: undefined,
  });
}

function renderMyBacklog() {
  return renderToStaticMarkup(
    <MemoryRouter>
      <MyBacklog />
    </MemoryRouter>,
  );
}

function renderMyBacklogInteractive() {
  return render(
    <MemoryRouter>
      <MyBacklog />
    </MemoryRouter>,
  );
}

describe("MyBacklog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaultMocks();
  });

  test("renders skeleton when data is loading", () => {
    const markup = renderMyBacklog();
    expect(markup).toContain("MuiSkeleton");
  });

  test("renders 404 create prompt when backlog not found", () => {
    mockGetMyBacklog.mockReturnValue({
      data: { response: { status: 404 } },
      isSuccess: false,
      refetch: vi.fn(),
    });

    const markup = renderMyBacklog();
    expect(markup).toContain("Create My Backlog");
  });

  test("renders create backlog loader when creating", () => {
    mockCreateMyBacklog.mockReturnValue({
      mutate: vi.fn(),
      isPending: true,
      isError: false,
    });

    const markup = renderMyBacklog();
    expect(markup).toContain("Creating your backlog");
  });

  test("renders error message when create fails", () => {
    mockCreateMyBacklog.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isError: true,
    });

    const markup = renderMyBacklog();
    expect(markup).toContain("Failed to create backlog");
  });

  test("renders empty state when no games", () => {
    mockGetMyBacklog.mockReturnValue({
      data: { data: { games: [] }, response: { status: 200 } },
      isSuccess: true,
      refetch: vi.fn(),
    });
    mockGetMyBacklogTab.mockReturnValue({
      data: { data: { games: [] }, response: { status: 200 } },
      isLoading: false,
      isFetching: false,
      isPlaceholderData: false,
    });

    const markup = renderMyBacklog();
    expect(markup).toContain("No games in your backlog");
  });

  test("renders My Backlog header when games exist", () => {
    const games = [
      {
        backlogGameId: 1,
        gameId: 10,
        title: "Hades",
        totalRating: 90,
        timeToBeat: 36000,
        genres: ["Action"],
        completedOn: null,
        removedOn: null,
        addedOn: "2025-01-01T00:00:00Z",
        igdbId: 100,
        steamAppId: 1000,
      },
    ];
    mockGetMyBacklog.mockReturnValue({
      data: { data: { games }, response: { status: 200 } },
      isSuccess: true,
      refetch: vi.fn(),
    });
    mockGetMyBacklogTab.mockReturnValue({
      data: { data: { games }, response: { status: 200 } },
      isLoading: false,
      isFetching: false,
      isPlaceholderData: false,
    });

    const markup = renderMyBacklog();
    expect(markup).toContain("My Backlog");
    expect(markup).toContain("Hades");
  });

  test("renders Refresh Backlog button", () => {
    const games = [
      {
        backlogGameId: 1,
        gameId: 10,
        title: "Hades",
        totalRating: 90,
        timeToBeat: 36000,
        genres: [],
        completedOn: null,
        removedOn: null,
        addedOn: "2025-01-01T00:00:00Z",
        igdbId: 100,
        steamAppId: 1000,
      },
    ];
    mockGetMyBacklog.mockReturnValue({
      data: { data: { games }, response: { status: 200 } },
      isSuccess: true,
      refetch: vi.fn(),
    });
    mockGetMyBacklogTab.mockReturnValue({
      data: { data: { games }, response: { status: 200 } },
      isLoading: false,
      isFetching: false,
      isPlaceholderData: false,
    });

    const markup = renderMyBacklog();
    expect(markup).toContain("Refresh Backlog");
  });

  test("shows Refreshing text when refresh is in progress", () => {
    mockRefreshMyBacklog.mockReturnValue({
      mutate: vi.fn(),
      isPending: true,
    });
    const games = [
      {
        backlogGameId: 1,
        gameId: 10,
        title: "Hades",
        totalRating: 90,
        timeToBeat: 36000,
        genres: [],
        completedOn: null,
        removedOn: null,
        addedOn: "2025-01-01T00:00:00Z",
        igdbId: 100,
        steamAppId: 1000,
      },
    ];
    mockGetMyBacklog.mockReturnValue({
      data: { data: { games }, response: { status: 200 } },
      isSuccess: true,
      refetch: vi.fn(),
    });
    mockGetMyBacklogTab.mockReturnValue({
      data: { data: { games }, response: { status: 200 } },
      isLoading: false,
      isFetching: false,
      isPlaceholderData: false,
    });

    const markup = renderMyBacklog();
    expect(markup).toContain("Refreshing…");
  });

  test("shows LinearProgress during refresh", () => {
    mockRefreshMyBacklog.mockReturnValue({
      mutate: vi.fn(),
      isPending: true,
    });
    const games = [
      {
        backlogGameId: 1,
        gameId: 10,
        title: "Hades",
        totalRating: 90,
        timeToBeat: 36000,
        genres: [],
        completedOn: null,
        removedOn: null,
        addedOn: "2025-01-01T00:00:00Z",
        igdbId: 100,
        steamAppId: 1000,
      },
    ];
    mockGetMyBacklog.mockReturnValue({
      data: { data: { games }, response: { status: 200 } },
      isSuccess: true,
      refetch: vi.fn(),
    });
    mockGetMyBacklogTab.mockReturnValue({
      data: { data: { games }, response: { status: 200 } },
      isLoading: false,
      isFetching: false,
      isPlaceholderData: false,
    });

    const markup = renderMyBacklog();
    expect(markup).toContain("MuiLinearProgress");
  });

  test("does not show LinearProgress when not refreshing", () => {
    const games = [
      {
        backlogGameId: 1,
        gameId: 10,
        title: "Hades",
        totalRating: 90,
        timeToBeat: 36000,
        genres: [],
        completedOn: null,
        removedOn: null,
        addedOn: "2025-01-01T00:00:00Z",
        igdbId: 100,
        steamAppId: 1000,
      },
    ];
    mockGetMyBacklog.mockReturnValue({
      data: { data: { games }, response: { status: 200 } },
      isSuccess: true,
      refetch: vi.fn(),
    });
    mockGetMyBacklogTab.mockReturnValue({
      data: { data: { games }, response: { status: 200 } },
      isLoading: false,
      isFetching: false,
      isPlaceholderData: false,
    });

    const markup = renderMyBacklog();
    expect(markup).not.toContain("MuiLinearProgress");
  });

  test("renders sort button group", () => {
    const games = [
      {
        backlogGameId: 1,
        gameId: 10,
        title: "Hades",
        totalRating: 90,
        timeToBeat: 36000,
        genres: [],
        completedOn: null,
        removedOn: null,
        addedOn: "2025-01-01T00:00:00Z",
        igdbId: 100,
        steamAppId: 1000,
      },
    ];
    mockGetMyBacklog.mockReturnValue({
      data: { data: { games }, response: { status: 200 } },
      isSuccess: true,
      refetch: vi.fn(),
    });
    mockGetMyBacklogTab.mockReturnValue({
      data: { data: { games }, response: { status: 200 } },
      isLoading: false,
      isFetching: false,
      isPlaceholderData: false,
    });

    const markup = renderMyBacklog();
    expect(markup).toContain("Score");
  });
});

function makeGames() {
  return [
    {
      backlogGameId: 1,
      gameId: 10,
      title: "Hades",
      totalRating: 90,
      timeToBeat: 36000,
      genres: ["Action"],
      completedOn: null,
      removedOn: null,
      addedOn: "2025-01-01T00:00:00Z",
      igdbId: 100,
      steamAppId: 1000,
      coverImageId: null,
      platformIds: [],
    },
    {
      backlogGameId: 2,
      gameId: 20,
      title: "Celeste",
      totalRating: 95,
      timeToBeat: 10800,
      genres: ["Platformer"],
      completedOn: null,
      removedOn: null,
      addedOn: "2025-02-01T00:00:00Z",
      igdbId: 200,
      steamAppId: 2000,
      coverImageId: null,
      platformIds: [],
    },
  ];
}

function setupGamesMocks(games = makeGames()) {
  const refetch = vi.fn();
  mockGetMyBacklog.mockReturnValue({
    data: { data: { games }, response: { status: 200 } },
    isSuccess: true,
    refetch,
  });
  mockGetMyBacklogTab.mockReturnValue({
    data: { data: { games }, response: { status: 200 } },
    isLoading: false,
    isFetching: false,
    isPreviousData: false,
    isPlaceholderData: false,
    dataUpdatedAt: Date.now(),
    refetch: vi.fn(),
  });
  mockCreateMyBacklog.mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
  });
  mockRefreshMyBacklog.mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
  });
  mockUpdateBacklogGame.mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
    variables: undefined,
  });
  return { refetch };
}

describe("MyBacklog interactions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("calls createBacklog mutate when Create My Backlog is clicked", () => {
    const mutate = vi.fn((_vars, opts) => opts?.onSuccess?.());
    const refetch = vi.fn();
    mockGetMyBacklog.mockReturnValue({
      data: { response: { status: 404 } },
      isSuccess: false,
      refetch,
    });
    mockGetMyBacklogTab.mockReturnValue({
      data: undefined,
      isLoading: true,
      isFetching: false,
      isPreviousData: false,
      isPlaceholderData: false,
    });
    mockCreateMyBacklog.mockReturnValue({
      mutate,
      isPending: false,
      isError: false,
    });
    mockRefreshMyBacklog.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
    mockUpdateBacklogGame.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      variables: undefined,
    });

    renderMyBacklogInteractive();
    fireEvent.click(screen.getByText("Create My Backlog"));
    expect(mutate).toHaveBeenCalled();
    expect(refetch).toHaveBeenCalled();
  });

  test("calls onError callback when createBacklog fails", () => {
    const mutate = vi.fn((_vars, opts) => opts?.onError?.());
    mockGetMyBacklog.mockReturnValue({
      data: { response: { status: 404 } },
      isSuccess: false,
      refetch: vi.fn(),
    });
    mockGetMyBacklogTab.mockReturnValue({
      data: undefined,
      isLoading: true,
      isFetching: false,
      isPreviousData: false,
      isPlaceholderData: false,
    });
    mockCreateMyBacklog.mockReturnValue({
      mutate,
      isPending: false,
      isError: false,
    });
    mockRefreshMyBacklog.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
    mockUpdateBacklogGame.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      variables: undefined,
    });

    renderMyBacklogInteractive();
    fireEvent.click(screen.getByText("Create My Backlog"));
    expect(mutate).toHaveBeenCalled();
  });

  test("calls refreshBacklog mutate when Refresh Backlog is clicked", () => {
    const mutate = vi.fn();
    setupGamesMocks();
    mockRefreshMyBacklog.mockReturnValue({
      mutate,
      isPending: false,
    });

    renderMyBacklogInteractive();
    fireEvent.click(screen.getByText("Refresh Backlog"));
    expect(mutate).toHaveBeenCalled();
  });

  test("calls setActiveTab when Completed Games tab is clicked", () => {
    const games = makeGames();
    const completedGames = [
      {
        ...games[0],
        backlogGameId: 3,
        title: "Completed Game",
        completedOn: "2025-06-01T00:00:00Z",
      },
    ];

    mockGetMyBacklog.mockReturnValue({
      data: { data: { games }, response: { status: 200 } },
      isSuccess: true,
      refetch: vi.fn(),
    });
    mockGetMyBacklogTab.mockImplementation((status: string) => ({
      data: {
        data: { games: status === "completed" ? completedGames : games },
        response: { status: 200 },
      },
      isLoading: false,
      isFetching: false,
      isPreviousData: false,
      isPlaceholderData: false,
      dataUpdatedAt: Date.now(),
      refetch: vi.fn(),
    }));
    mockCreateMyBacklog.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isError: false,
    });
    mockRefreshMyBacklog.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
    mockUpdateBacklogGame.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      variables: undefined,
    });

    renderMyBacklogInteractive();
    fireEvent.click(screen.getByRole("tab", { name: /completed games/i }));
    expect(screen.getByText("Completed Game")).toBeInTheDocument();
  });

  test("sorts games by time when Shortest Time button is clicked", () => {
    setupGamesMocks();

    renderMyBacklogInteractive();
    fireEvent.click(screen.getByText("⏱️ Shortest Time"));
    const titles = screen
      .getAllByText(/Hades|Celeste/)
      .map((el) => el.textContent);
    expect(titles[0]).toBe("Celeste");
    expect(titles[1]).toBe("Hades");
  });

  test("sorts games by blended when Blended button is clicked", () => {
    setupGamesMocks();

    renderMyBacklogInteractive();
    fireEvent.click(screen.getByText("🎯 Blended"));
    const listItems = screen.getAllByText(/Hades|Celeste/);
    expect(listItems.length).toBeGreaterThanOrEqual(2);
  });

  test("calls updateBacklogGame when Mark complete is clicked", () => {
    const mutate = vi.fn((_vars, opts) => opts?.onSuccess?.());
    setupGamesMocks();
    mockUpdateBacklogGame.mockReturnValue({
      mutate,
      isPending: false,
      variables: undefined,
    });

    renderMyBacklogInteractive();
    const markButtons = screen.getAllByRole("button", {
      name: /mark complete/i,
    });
    fireEvent.click(markButtons[0]);
    expect(mutate).toHaveBeenCalled();
  });

  test("opens remove dialog when Remove from backlog is clicked", () => {
    setupGamesMocks();
    mockUpdateBacklogGame.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      variables: undefined,
    });

    renderMyBacklogInteractive();
    const removeButtons = screen.getAllByRole("button", {
      name: /remove from backlog/i,
    });
    fireEvent.click(removeButtons[0]);
    expect(screen.getByText("Remove game from backlog?")).toBeInTheDocument();
  });

  test("calls updateBacklogGame with removedOn when remove is confirmed", () => {
    const mutate = vi.fn((_vars, opts) => opts?.onSuccess?.());
    setupGamesMocks();
    mockUpdateBacklogGame.mockReturnValue({
      mutate,
      isPending: false,
      variables: undefined,
    });

    renderMyBacklogInteractive();
    const removeButtons = screen.getAllByRole("button", {
      name: /remove from backlog/i,
    });
    fireEvent.click(removeButtons[0]);
    fireEvent.click(screen.getByRole("button", { name: /^remove$/i }));
    expect(mutate).toHaveBeenCalled();
    expect(mockQueryClient.invalidateQueries).toHaveBeenCalled();
  });

  test("tab switch triggers refetch when dataUpdatedAt > 0", () => {
    const refetchActive = vi.fn();
    const refetchCompleted = vi.fn();
    const games = makeGames();
    const completedGames = [
      {
        ...games[0],
        backlogGameId: 3,
        title: "Completed Game",
        completedOn: "2025-06-01T00:00:00Z",
      },
    ];

    mockGetMyBacklog.mockReturnValue({
      data: { data: { games }, response: { status: 200 } },
      isSuccess: true,
      refetch: vi.fn(),
    });
    mockGetMyBacklogTab.mockImplementation((status: string) => ({
      data: {
        data: { games: status === "completed" ? completedGames : games },
        response: { status: 200 },
      },
      isLoading: false,
      isFetching: false,
      isPreviousData: false,
      isPlaceholderData: false,
      dataUpdatedAt: Date.now(),
      refetch: status === "active" ? refetchActive : refetchCompleted,
    }));
    mockCreateMyBacklog.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isError: false,
    });
    mockRefreshMyBacklog.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
    mockUpdateBacklogGame.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      variables: undefined,
    });

    renderMyBacklogInteractive();
    fireEvent.click(screen.getByRole("tab", { name: /completed games/i }));
    expect(refetchCompleted).toHaveBeenCalled();
  });
});
