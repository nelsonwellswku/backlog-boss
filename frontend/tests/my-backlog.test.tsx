import { renderToStaticMarkup } from "react-dom/server";
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
