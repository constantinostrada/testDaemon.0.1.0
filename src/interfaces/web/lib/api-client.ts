/**
 * api-client.ts
 * =============
 * Typed HTTP client for the Mini-Library FastAPI backend.
 *
 * Responsibilities:
 *   - Centralise all fetch() calls to the backend.
 *   - Provide strongly-typed request/response interfaces.
 *   - Surface HTTP errors as typed ApiError instances.
 *
 * This module has NO business logic — it is purely an infrastructure
 * adapter for the frontend.
 */

// ---------------------------------------------------------------------------
// Base URL
// ---------------------------------------------------------------------------

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ---------------------------------------------------------------------------
// Response types (mirror the FastAPI schemas)
// ---------------------------------------------------------------------------

export type BookStatus = "unread" | "reading" | "read";

export interface Book {
  id: string;
  title: string;
  authors: string[];
  isbn: string;
  genre: string;
  status: BookStatus;
  year_published: number | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedBooks {
  books: Book[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface AddBookPayload {
  title: string;
  authors: string[];
  isbn: string;
  genre: string;
  year_published?: number | null;
}

export interface UpdateBookStatusPayload {
  status: BookStatus;
}

export interface SearchBooksParams {
  title?: string;
  author?: string;
  year?: number;
  limit?: number;
  offset?: number;
}

// ---------------------------------------------------------------------------
// Error type
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  constructor(
    public readonly statusCode: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// ---------------------------------------------------------------------------
// Fetch helper
// ---------------------------------------------------------------------------

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (response.status === 204) {
    return {} as T;
  }

  const data: unknown = await response.json();

  if (!response.ok) {
    const detail =
      typeof data === "object" && data !== null && "detail" in data
        ? String((data as Record<string, unknown>).detail)
        : response.statusText;
    throw new ApiError(response.status, detail);
  }

  return data as T;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export const booksApi = {
  /**
   * Fetch a paginated list of books.
   */
  list(params?: {
    status?: BookStatus;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedBooks> {
    const query = new URLSearchParams();
    if (params?.status) query.set("status_filter", params.status);
    if (params?.limit !== undefined) query.set("limit", String(params.limit));
    if (params?.offset !== undefined) query.set("offset", String(params.offset));
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<PaginatedBooks>(`/api/v1/books${qs}`);
  },

  /**
   * Search the catalogue by title (substring), author (substring), and/or year (exact).
   * Backend AND-s any provided criteria; missing/empty fields are ignored.
   */
  search(params: SearchBooksParams): Promise<PaginatedBooks> {
    const query = new URLSearchParams();
    if (params.title) query.set("title", params.title);
    if (params.author) query.set("author", params.author);
    if (params.year !== undefined) query.set("year", String(params.year));
    if (params.limit !== undefined) query.set("limit", String(params.limit));
    if (params.offset !== undefined) query.set("offset", String(params.offset));
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<PaginatedBooks>(`/api/v1/books/search${qs}`);
  },

  /**
   * Fetch a single book by ID.
   */
  getById(id: string): Promise<Book> {
    return request<Book>(`/api/v1/books/${encodeURIComponent(id)}`);
  },

  /**
   * Add a new book to the library.
   */
  add(payload: AddBookPayload): Promise<Book> {
    return request<Book>("/api/v1/books", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  /**
   * Update the reading status of a book.
   */
  updateStatus(id: string, payload: UpdateBookStatusPayload): Promise<Book> {
    return request<Book>(`/api/v1/books/${encodeURIComponent(id)}/status`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  /**
   * Delete a book from the library.
   */
  delete(id: string): Promise<void> {
    return request<void>(`/api/v1/books/${encodeURIComponent(id)}`, {
      method: "DELETE",
    });
  },
};
