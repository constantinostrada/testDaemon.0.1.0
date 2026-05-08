"use client";

/**
 * BookList Component
 * ==================
 * Renders the catalog screen: a debounced search input on top and an
 * incremental list of books underneath. Behaviour:
 *
 *  - User types in the search input → after 300ms of inactivity the
 *    component fires GET /api/v1/books/search?title=<query>. While the
 *    user keeps typing, no request is in flight.
 *  - When the input is empty, the component falls back to GET
 *    /api/v1/books (the full paginated catalog).
 *  - Long catalogs are not rendered all at once: results come in pages
 *    of PAGE_SIZE and a "Load more" button appends the next page using
 *    `has_more` / `offset` from the API.
 *  - Loading, error and empty states are visible.
 *
 * This is a client component because it manages local state.
 */

import { useEffect, useState, useCallback, useRef } from "react";
import type { Book, BookStatus, PaginatedBooks } from "@/lib/api-client";
import { booksApi, ApiError } from "@/lib/api-client";
import BookCard from "@/components/BookCard";

interface BookListProps {
  initialData: PaginatedBooks;
}

const PAGE_SIZE = 20;
const DEBOUNCE_MS = 300;

async function fetchPage(
  query: string,
  offset: number,
): Promise<PaginatedBooks> {
  const trimmed = query.trim();
  if (trimmed === "") {
    return booksApi.list({ limit: PAGE_SIZE, offset });
  }
  return booksApi.search({ title: trimmed, limit: PAGE_SIZE, offset });
}

export default function BookList({ initialData }: BookListProps): JSX.Element {
  const [books, setBooks] = useState<Book[]>(initialData.books);
  const [total, setTotal] = useState<number>(initialData.total);
  const [hasMore, setHasMore] = useState<boolean>(initialData.has_more);
  const [offset, setOffset] = useState<number>(initialData.offset + initialData.books.length);
  const [query, setQuery] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // We skip the debounced effect's first run so that the initial
  // server-rendered data isn't immediately overwritten by a client fetch.
  const isFirstRender = useRef<boolean>(true);

  // Debounced search: when `query` changes, wait DEBOUNCE_MS then fetch.
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    const handle = setTimeout(() => {
      void (async (): Promise<void> => {
        setLoading(true);
        setError(null);
        try {
          const data = await fetchPage(query, 0);
          setBooks(data.books);
          setTotal(data.total);
          setHasMore(data.has_more);
          setOffset(data.books.length);
        } catch (err) {
          setError(err instanceof ApiError ? err.message : "Failed to load books.");
          setBooks([]);
          setTotal(0);
          setHasMore(false);
          setOffset(0);
        } finally {
          setLoading(false);
        }
      })();
    }, DEBOUNCE_MS);

    return () => clearTimeout(handle);
  }, [query]);

  const handleLoadMore = useCallback(async (): Promise<void> => {
    setLoadingMore(true);
    setError(null);
    try {
      const data = await fetchPage(query, offset);
      setBooks((prev) => [...prev, ...data.books]);
      setHasMore(data.has_more);
      setOffset((prev) => prev + data.books.length);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load more books.");
    } finally {
      setLoadingMore(false);
    }
  }, [query, offset]);

  const handleDelete = async (id: string): Promise<void> => {
    if (!confirm("Are you sure you want to remove this book?")) return;
    try {
      await booksApi.delete(id);
      setBooks((prev) => prev.filter((b) => b.id !== id));
      setTotal((prev) => Math.max(0, prev - 1));
      setOffset((prev) => Math.max(0, prev - 1));
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

  const trimmedQuery = query.trim();

  return (
    <div className="mt-2">
      {/* Search bar */}
      <div className="form-group">
        <label htmlFor="catalog-search" className="form-label">
          Search the catalogue
        </label>
        <input
          id="catalog-search"
          type="search"
          role="searchbox"
          className="form-input w-full"
          placeholder="Search by title…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search by title"
          autoComplete="off"
        />
        <span className="text-muted text-sm">
          {total} book{total !== 1 ? "s" : ""}
          {trimmedQuery !== "" && ` matching “${trimmedQuery}”`}
        </span>
      </div>

      {/* Error */}
      {error && (
        <div className="alert alert-error" role="alert">
          {error}
        </div>
      )}

      {/* Loading (full reload) */}
      {loading && (
        <p
          className="text-muted text-sm"
          role="status"
          aria-live="polite"
          style={{ marginBottom: "1rem" }}
        >
          Loading…
        </p>
      )}

      {/* Empty state */}
      {!loading && !error && books.length === 0 && (
        <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
          <p style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>📚</p>
          <p className="text-muted">
            {trimmedQuery === ""
              ? "Your library is empty. Add your first book!"
              : `No books match “${trimmedQuery}”.`}
          </p>
          {trimmedQuery === "" && (
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

      {/* Load more */}
      {hasMore && books.length > 0 && (
        <div className="flex justify-between" style={{ marginTop: "1.25rem", justifyContent: "center" }}>
          <button
            type="button"
            onClick={() => void handleLoadMore()}
            className="btn btn-ghost"
            disabled={loadingMore}
          >
            {loadingMore ? "Loading…" : "Load more"}
          </button>
        </div>
      )}
    </div>
  );
}
