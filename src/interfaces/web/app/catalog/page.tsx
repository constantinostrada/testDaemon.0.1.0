"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Book, PaginatedBooks } from "@/lib/api-client";
import { booksApi, ApiError } from "@/lib/api-client";

const PAGE_SIZE = 20;
const DEBOUNCE_MS = 300;

export default function CatalogPage(): JSX.Element {
  const [input, setInput] = useState<string>("");
  const [query, setQuery] = useState<string>("");
  const [books, setBooks] = useState<Book[]>([]);
  const [offset, setOffset] = useState<number>(0);
  const [total, setTotal] = useState<number>(0);
  const [hasMore, setHasMore] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const requestIdRef = useRef<number>(0);

  useEffect(() => {
    const handle = setTimeout((): void => setQuery(input.trim()), DEBOUNCE_MS);
    return (): void => clearTimeout(handle);
  }, [input]);

  const fetchPage = useCallback(
    async (q: string, currentOffset: number, append: boolean): Promise<void> => {
      const requestId = ++requestIdRef.current;
      setLoading(true);
      setError(null);
      try {
        const data: PaginatedBooks = q
          ? await booksApi.search({ title: q, limit: PAGE_SIZE, offset: currentOffset })
          : await booksApi.list({ limit: PAGE_SIZE, offset: currentOffset });

        if (requestId !== requestIdRef.current) return;

        setBooks((prev) => (append ? [...prev, ...data.books] : data.books));
        setOffset(currentOffset + data.books.length);
        setTotal(data.total);
        setHasMore(data.has_more);
      } catch (err) {
        if (requestId !== requestIdRef.current) return;
        setError(
          err instanceof ApiError
            ? `Failed to load catalog: ${err.message}`
            : "Failed to load catalog. The server may be unavailable.",
        );
        if (!append) {
          setBooks([]);
          setTotal(0);
          setHasMore(false);
        }
      } finally {
        if (requestId === requestIdRef.current) setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    void fetchPage(query, 0, false);
  }, [query, fetchPage]);

  useEffect(() => {
    const node = sentinelRef.current;
    if (!node) return;
    if (!hasMore || loading) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (entry?.isIntersecting && hasMore && !loading) {
          void fetchPage(query, offset, true);
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(node);
    return (): void => observer.disconnect();
  }, [hasMore, loading, offset, query, fetchPage]);

  return (
    <div className="mt-2">
      <div
        className="flex items-center justify-between"
        style={{ marginBottom: "1rem", gap: "1rem" }}
      >
        <h2 style={{ margin: 0 }}>Catalog</h2>
        <a href="/add" className="btn btn-primary" data-testid="catalog-add-book-link">
          + Add Book
        </a>
      </div>

      <div className="form-group">
        <input
          type="search"
          className="form-input"
          placeholder="Search by title…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          aria-label="Search catalog by title"
        />
        <span className="text-muted text-sm">
          {total} book{total !== 1 ? "s" : ""}
          {query && ` matching “${query}”`}
        </span>
      </div>

      {error && (
        <div className="alert alert-error" role="alert">
          {error}
        </div>
      )}

      {!loading && !error && books.length === 0 && (
        <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
          <p style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>📚</p>
          <p className="text-muted">
            {query ? `No books match “${query}”.` : "The catalog is empty."}
          </p>
        </div>
      )}

      <ul
        style={{
          listStyle: "none",
          padding: 0,
          margin: 0,
          display: "flex",
          flexDirection: "column",
          gap: "0.5rem",
        }}
      >
        {books.map((book) => (
          <li key={book.id} className="card" style={{ padding: "0.75rem 1rem" }}>
            <div className="flex items-center justify-between" style={{ gap: "1rem" }}>
              <div style={{ minWidth: 0, flex: 1 }}>
                <h3 style={{ fontWeight: 600, fontSize: "1rem", lineHeight: 1.3 }}>
                  {book.title}
                </h3>
                <p className="text-muted text-sm" style={{ marginTop: "0.2rem" }}>
                  by {book.authors.join(", ")}
                </p>
              </div>
              {book.year_published !== null && (
                <span className="text-muted text-sm" aria-label="year published">
                  {book.year_published}
                </span>
              )}
            </div>
          </li>
        ))}
      </ul>

      {loading && (
        <p
          className="text-muted text-sm"
          role="status"
          style={{ textAlign: "center", padding: "1rem" }}
        >
          Loading…
        </p>
      )}

      <div ref={sentinelRef} aria-hidden="true" style={{ height: "1px" }} />
    </div>
  );
}
