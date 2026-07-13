import { render, screen } from "@testing-library/react";
import { CoverImage } from "../src/components/CoverImage";

describe("CoverImage", () => {
  test("renders img when imageId is provided", () => {
    render(<CoverImage imageId="abc123" title="Test Game" />);
    const img = screen.getByRole("img", { name: "Test Game" });
    expect(img).toHaveAttribute(
      "src",
      "https://images.igdb.com/igdb/image/upload/t_cover_big/abc123.jpg",
    );
  });

  test("renders placeholder when imageId is null", () => {
    render(<CoverImage imageId={null} title="Test Game" />);
    expect(screen.getByText("T")).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  test("renders placeholder when imageId is undefined", () => {
    render(<CoverImage title="Test Game" />);
    expect(screen.getByText("T")).toBeInTheDocument();
  });

  test("uppercases first letter in placeholder", () => {
    render(<CoverImage imageId={null} title="my game" />);
    expect(screen.getByText("M")).toBeInTheDocument();
  });
});
