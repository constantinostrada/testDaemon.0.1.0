/**
 * Unit tests for the BookCard component.
 */

import { render, screen, fireEvent } from "@testing-library/react";
import BookCard from "@/components/BookCard";
import type { Book } from "@/lib/api-client";

const mockBook: Book = {
  id: "abc-123",
  title: "Clean Code",
  author: "Robert C. Martin",
  isbn: "9780132350884",
  status: "unread",
  year_published: 2008,
  description: "A handbook of agile software craftsmanship.",
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

describe("BookCard", () => {
  it("renders the book title and author", () => {
    render(
      <BookCard
        book={mockBook}
        onDelete={jest.fn()}
        onStatusChange={jest.fn()}
      />,
    );
    expect(screen.getByText("Clean Code")).toBeInTheDocument();
    expect(screen.getByText("by Robert C. Martin")).toBeInTheDocument();
  });

  it("shows the unread status badge", () => {
    render(
      <BookCard
        book={mockBook}
        onDelete={jest.fn()}
        onStatusChange={jest.fn()}
      />,
    );
    expect(screen.getByText("Unread")).toBeInTheDocument();
  });

  it("calls onStatusChange when action button is clicked", () => {
    const onStatusChange = jest.fn().mockResolvedValue(undefined);
    render(
      <BookCard
        book={mockBook}
        onDelete={jest.fn()}
        onStatusChange={onStatusChange}
      />,
    );
    const btn = screen.getByText("Start Reading →");
    fireEvent.click(btn);
    expect(onStatusChange).toHaveBeenCalledWith("abc-123", "reading");
  });

  it("calls onDelete when delete button is clicked", () => {
    const onDelete = jest.fn().mockResolvedValue(undefined);
    // Mock window.confirm
    window.confirm = jest.fn(() => true);
    render(
      <BookCard
        book={mockBook}
        onDelete={onDelete}
        onStatusChange={jest.fn()}
      />,
    );
    const deleteBtn = screen.getByTitle("Remove from library");
    fireEvent.click(deleteBtn);
    expect(onDelete).toHaveBeenCalledWith("abc-123");
  });

  it("shows no action button for READ books (terminal state)", () => {
    const readBook: Book = { ...mockBook, status: "read" };
    render(
      <BookCard
        book={readBook}
        onDelete={jest.fn()}
        onStatusChange={jest.fn()}
      />,
    );
    expect(screen.queryByText("Start Reading →")).not.toBeInTheDocument();
    expect(screen.queryByText("Mark as Read ✓")).not.toBeInTheDocument();
  });
});
