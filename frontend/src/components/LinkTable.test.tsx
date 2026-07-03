import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import LinkTable from "./LinkTable";

describe("LinkTable", () => {
  it("shows an empty state when there are no links", () => {
    render(<LinkTable links={[]} />);
    expect(screen.getByText(/no links yet/i)).toBeTruthy();
  });

  it("renders a row per link", () => {
    render(
      <LinkTable
        links={[
          {
            id: 1,
            code: "abc123",
            long_url: "https://example.com",
            short_url: "http://localhost:8000/abc123",
            created_at: "2026-07-03T00:00:00Z",
          },
        ]}
      />,
    );
    expect(screen.getByText("/abc123")).toBeTruthy();
    expect(screen.getByText("https://example.com")).toBeTruthy();
  });
});
