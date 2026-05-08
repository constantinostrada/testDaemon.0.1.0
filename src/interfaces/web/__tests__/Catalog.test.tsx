/**
 * Unit tests for the Catalog page.
 *
 * Validates the AC for "Pantalla del catálogo":
 *   - title / authors / year are visible
 *   - search input is real-time and debounced (no fetch storm)
 *   - non-empty query hits the search endpoint, empty hits list
 *   - infinite scroll loads further pages on intersection
 *   - API failures surface as a visible error
 *   - loading state is visible while in flight
 */

import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import CatalogPage from "@/app/catalog/page";

// ---------------------------------------------------------------------------
// IntersectionObserver polyfill (jsdom does not ship one).
// We capture the most recent callback so tests can fire intersections at will.
// ---------------------------------------------------------------------------

interface MockObserverInstance {
  callback: IntersectionObserverCallback;
  observe: jest.Mock;
  unobserve: jest.Mock;
  disconnect: jest.Mock;
}

let lastObserver: MockObserverInstance | null = null;

class MockIntersectionObserver implements IntersectionObserver {
  readonly root: Element | Document | null = null;
  readonly rootMargin: string = "";
  readonly thresholds: ReadonlyArray<number> = [];
  private readonly _instance: MockObserverInstance;

  constructor(callback: IntersectionObserverCallback) {
    this._instance = {
      callback,
      observe: jest.fn(),
      unobserve: jest.fn(),
      disconnect: jest.fn(),
    };
    lastObserver = this._instance;
  }

  observe(target: Element): void {
    this._instance.observe(target);
  }
  unobserve(target: Element): void {
    this._instance.unobserve(target);
  }
  disconnect(): void {
    this._instance.disconnect();
  }
  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

interface BookFixture {
  id: string;
  title: string;
  authors: string[];
  isbn: string;
  genre: string;
  status: "unread" | "reading" | "read";
  year_published: number | null;
  created_at: string;
  updated_at: string;
}

function makeBook(overrides: Partial<BookFixture> = {}): BookFixture {
  return {
    id: "id-" + Math.random().toString(36).slice(2, 8),
    title: "Untitled",
    authors: ["Anon"],
    isbn: "9780000000000",
    genre: "General",
    status: "unread",
    year_published: 2020,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
    ...overrides,
  };
}

function pageResponse(books: BookFixture[], total: number, offset: number, hasMore: boolean) {
  return {
    books,
    total,
    limit: 20,
    offset,
    has_more: hasMore,
  };
}

function jsonResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? "OK" : "Error",
    json: () => Promise.resolve(body),
  } as unknown as Response;
}

function fireIntersect(): void {
  if (!lastObserver) throw new Error("No IntersectionObserver was created");
  act(() => {
    lastObserver!.callback(
      [{ isIntersecting: true } as IntersectionObserverEntry],
      lastObserver as unknown as IntersectionObserver,
    );
  });
}

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------

const fetchMock = jest.fn();

beforeAll(() => {
  (global as unknown as { IntersectionObserver: unknown }).IntersectionObserver =
    MockIntersectionObserver;
});

beforeEach(() => {
  fetchMock.mockReset();
  lastObserver = null;
  (global as unknown as { fetch: unknown }).fetch = fetchMock;
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("CatalogPage", () => {
  it("renders title, authors and year for each book on initial load", async () => {
    const books = [
      makeBook({ id: "1", title: "Clean Code", authors: ["Robert C. Martin"], year_published: 2008 }),
      makeBook({
        id: "2",
        title: "The Pragmatic Programmer",
        authors: ["David Thomas", "Andrew Hunt"],
        year_published: 1999,
      }),
    ];
    fetchMock.mockResolvedValueOnce(jsonResponse(pageResponse(books, 2, 0, false)));

    render(<CatalogPage />);

    expect(await screen.findByText("Clean Code")).toBeInTheDocument();
    expect(screen.getByText("by Robert C. Martin")).toBeInTheDocument();
    expect(screen.getByText("2008")).toBeInTheDocument();

    expect(screen.getByText("The Pragmatic Programmer")).toBeInTheDocument();
    expect(screen.getByText("by David Thomas, Andrew Hunt")).toBeInTheDocument();
    expect(screen.getByText("1999")).toBeInTheDocument();
  });

  it("debounces typing so the API is not hit on every keystroke", async () => {
    jest.useFakeTimers();
    fetchMock.mockResolvedValue(jsonResponse(pageResponse([], 0, 0, false)));
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });

    render(<CatalogPage />);

    // Initial empty-query fetch (list endpoint).
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    expect(fetchMock.mock.calls[0][0]).toContain("/api/v1/books");
    expect(fetchMock.mock.calls[0][0]).not.toContain("/search");

    const searchInput = screen.getByLabelText(/search catalog by title/i);

    // Five quick keystrokes — must NOT trigger five fetches.
    await user.type(searchInput, "clean");

    // Before the debounce window elapses, no extra fetch.
    expect(fetchMock).toHaveBeenCalledTimes(1);

    // Advance past the debounce.
    await act(async () => {
      jest.advanceTimersByTime(350);
    });

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    const secondCallUrl = String(fetchMock.mock.calls[1][0]);
    expect(secondCallUrl).toContain("/api/v1/books/search");
    expect(secondCallUrl).toContain("title=clean");

    jest.useRealTimers();
  });

  it("shows a loading indicator while the request is in flight", async () => {
    let resolveFetch: ((value: Response) => void) | undefined;
    fetchMock.mockImplementationOnce(
      () =>
        new Promise<Response>((resolve) => {
          resolveFetch = resolve;
        }),
    );

    render(<CatalogPage />);

    expect(await screen.findByRole("status")).toHaveTextContent(/loading/i);

    act(() => {
      resolveFetch?.(jsonResponse(pageResponse([], 0, 0, false)));
    });

    await waitFor(() => expect(screen.queryByRole("status")).not.toBeInTheDocument());
  });

  it("shows an error alert when the API is unavailable", async () => {
    fetchMock.mockRejectedValueOnce(new TypeError("Failed to fetch"));

    render(<CatalogPage />);

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/failed to load catalog/i);
  });

  it("loads the next page through infinite scroll with the correct offset", async () => {
    const firstPage = Array.from({ length: 20 }, (_, i) =>
      makeBook({ id: `b${i}`, title: `Book ${i}` }),
    );
    const secondPage = [makeBook({ id: "b20", title: "Book 20" })];

    fetchMock
      .mockResolvedValueOnce(jsonResponse(pageResponse(firstPage, 21, 0, true)))
      .mockResolvedValueOnce(jsonResponse(pageResponse(secondPage, 21, 20, false)));

    render(<CatalogPage />);

    await screen.findByText("Book 0");
    expect(screen.queryByText("Book 20")).not.toBeInTheDocument();

    await waitFor(() => expect(lastObserver).not.toBeNull());

    fireIntersect();

    await screen.findByText("Book 20");
    expect(fetchMock).toHaveBeenCalledTimes(2);
    const secondCallUrl = String(fetchMock.mock.calls[1][0]);
    expect(secondCallUrl).toContain("offset=20");
  });

  it("uses the search endpoint when the user types a non-empty query", async () => {
    jest.useFakeTimers();
    fetchMock.mockResolvedValue(jsonResponse(pageResponse([], 0, 0, false)));
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });

    render(<CatalogPage />);

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));

    const searchInput = screen.getByLabelText(/search catalog by title/i);
    await user.type(searchInput, "py");

    await act(async () => {
      jest.advanceTimersByTime(350);
    });

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    const url = String(fetchMock.mock.calls[1][0]);
    expect(url).toMatch(/\/api\/v1\/books\/search\?.*title=py/);

    jest.useRealTimers();
  });
});
