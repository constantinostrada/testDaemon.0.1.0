"use client";

/**
 * BookList Component
 * ==================
 * Renders the library book list with status filtering and inline actions.
 * This is a client component because it manages local state.
 */

import { useState, useCallback } from "react";
import type { Book, BookStatus, PaginatedBooks } from "@/lib/api-client";
import { booksApi, ApiError } from "@/lib/api-client";
import BookCard from "@/components/BookCard";

interface BookListProps {
  initialData: PaginatedBooks;
}

const STATUS_FILTERS: Array<{ label: string; value: BookStatus | "all" }> = [
  { label: "All", value: "all" },
  { label: "📖 Unread", value: "unread" },
  { label: "🔖 Reading", value: "reading" },
  { label: "✅ Read", value: "read" },
];

export default function BookList({ initialData }: BookListProps): JSX.Element {
  const [books, setBooks] = useState<Book[]>(initialData.books);
  const [total, setTotal] = useState<number>(initialData.total);
  const [filter, setFilter] = useState<BookStatus | "all">("all");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBooks = useCallback(async (statusFilter: BookStatus | "all"): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const data = await booksApi.list({
        status: statusFilter === "all" ? undefined : statusFilter,
        limit: 50,
      });
      setBooks(data.books);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load books.");
    } finally {
      setLoading(false);
    }
  }, []);

  const handleFilterChange = (newFilter: BookStatus | "all"): void => {
    setFilter(newFilter);
    void fetchBooks(newFilter);
  };

  const handleDelete = async (id: string): Promise<void> => {
    if (!confirm("Are you sure you want to remove this book?")) return;
    try {
      await booksApi.delete(id);
      setBooks((prev) => prev.filter((b) => b.id !== id));
      setTotal((prev) => prev - 1);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to delete book.");
    }
  };

  const handleStatusChange = async (id: string, newStatus: BookStatus): Promise<void> => {
    try {
      const updated = await booksApi.updateStatus(id, { status: newStatus });
      setBooks((prev) => prev.map((b) => (b.id === id ? updated : b)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to update status.");
    }
  };

  return (
    <div className="mt-2">
      {/* Filter tabs */}
      <div className="flex gap-2" style={{ marginBottom: "1.25rem", flexWrap: "wrap" }}>
        {STATUS_FILTERS.map(({ label, value }) => (
          <button
            key={value}
            onClick={() => handleFilterChange(value)}
            className={`btn ${filter === value ? "btn-primary" : "btn-ghost"}`}
            style={{ fontSize: "0.85rem", padding: "0.4rem 1rem" }}
          >
            {label}
          </button>
        ))}
        <span className="text-muted text-sm" style={{ alignSelf: "center", marginLeft: "auto" }}>
          {total} book{total !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Error */}
      {error && <div className="alert alert-error">{error}</div>}

      {/* Loading */}
      {loading && (
        <p className="text-muted text-sm" style={{ marginBottom: "1rem" }}>
          Loading…
        </p>
      )}

      {/* Empty state */}
      {!loading && books.length === 0 && (
        <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
          <p style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>📚</p>
          <p className="text-muted">
            {filter === "all"
              ? "Your library is empty. Add your first book!"
              : `No books with status "${filter}".`}
          </p>
          {filter === "all" && (
            <a href="/add" className="btn btn-primary" style={{ marginTop: "1rem" }}>
              + Add Book
            </a>
          )}
        </div>
      )}

      {/* Book grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: "1rem",
        }}
      >
        {books.map((book) => (
          <BookCard
            key={book.id}
            book={book}
            onDelete={handleDelete}
            onStatusChange={handleStatusChange}
          />
        ))}
      </div>
    </div>
  );
}
