import { render, screen, act } from "@testing-library/react";
import { vi, describe, test, expect, afterEach } from "vitest";

import { BacklogCreatingLoader } from "../src/pages/my-backlog/BacklogCreatingLoader";

afterEach(() => {
  vi.useRealTimers();
});

describe("BacklogCreatingLoader", () => {
  test("renders initial creation message", () => {
    render(<BacklogCreatingLoader />);
    expect(screen.getByText("Creating your backlog...")).toBeInTheDocument();
  });

  test("renders 'This will only take a moment' subtitle", () => {
    render(<BacklogCreatingLoader />);
    expect(
      screen.getByText("This will only take a moment"),
    ).toBeInTheDocument();
  });

  test("renders CircularProgress", () => {
    const { container } = render(<BacklogCreatingLoader />);
    expect(container.querySelector("svg")).toBeInTheDocument();
  });

  test("advances to next message after 5 seconds", () => {
    vi.useFakeTimers();
    render(<BacklogCreatingLoader />);

    expect(screen.getByText("Creating your backlog...")).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(5000);
    });

    expect(
      screen.getByText("Fetching your games from Steam..."),
    ).toBeInTheDocument();
  });

  test("advances through all creation messages", () => {
    vi.useFakeTimers();
    render(<BacklogCreatingLoader />);

    const messages = [
      "Creating your backlog...",
      "Fetching your games from Steam...",
      "Fetching game ratings...",
      "Fetching game times to beat...",
      "Finalizing your backlog...",
    ];

    for (let i = 0; i < messages.length; i++) {
      expect(screen.getByText(messages[i])).toBeInTheDocument();
      if (i < messages.length - 1) {
        act(() => {
          vi.advanceTimersByTime(5000);
        });
      }
    }
  });

  test("stays on last message after all intervals", () => {
    vi.useFakeTimers();
    render(<BacklogCreatingLoader />);

    for (let i = 0; i < 10; i++) {
      act(() => {
        vi.advanceTimersByTime(5000);
      });
    }

    expect(screen.getByText("Finalizing your backlog...")).toBeInTheDocument();
  });

  test("cleans up interval on unmount", () => {
    vi.useFakeTimers();
    const clearIntervalSpy = vi.spyOn(global, "clearInterval");
    const { unmount } = render(<BacklogCreatingLoader />);

    unmount();

    expect(clearIntervalSpy).toHaveBeenCalled();
    clearIntervalSpy.mockRestore();
  });
});
