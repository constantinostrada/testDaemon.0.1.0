/**
 * Unit tests for the BookList component.
 *
 * Covers the catalog screen acceptance criteria:
 *   - Listing shows title, author(s) and year.
 *   - Typing in the search filters in real time, no "search" button.
 *   - Search is debounced (no request per keystroke).
 *   - Incremental rendering: a "Load more" button appends pages.
 *   - Visible loading feedback and an error state when the API fails.
 */

import { act, render, screen, fireEvent } from "@testing-library/react";
import type { Book, PaginatedBooks } from "@/lib/api-client";

jest.mock("@/lib/api-client", () => {
  class ApiError extends Error {
    constructor(public statusCode: number, message: string) {
      super(message);
      this.name = "ApiError";
    }
  }
  return {
    __esModule: true,
    ApiError,
    booksApi: {
      list: jest.fn(),
      search: jest.fn(),
      updateStatus: jest.fn(),
      delete: jest.fn(),
    },
  };
});

import { booksApi, ApiError } from "@/lib/api-client";
import BookList from "@/components/BookList";

const mockedList = booksApi.list as jest.MockedFunction<typeof booksApi.list>;
const mockedSearch = booksApi.search as jest.MockedFunction<typeof booksApi.search>;

function makeBook(overrides: Partial<Book> = {}): Book {
  return {
    id: overrides.id ?? "id-1",
    title: overrides.title ?? "Clean Code",
    authors: overrides.authors ?? ["Robert C. Martin"],
    isbn: overrides.isbn ?? "9780132350884",
    genre: overrides.genre ?? "Software",
    status: overrides.status ?? "unread",
    year_published: overrides.year_published ?? 2008,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  };
}

function makePage(books: Book[], offset: number, total: number, hasMore: boolean): PaginatedBooks {
  return { books, total, limit: 20, offset, has_more: hasMore };
}

const initialBook = makeBook({ id: "init-1", title: "Refactoring", authors: ["Martin Fowler"], year_published: 1999 });

const initialData: PaginatedBooks = makePage([initialBook], 0, 1, false);

beforeEach(() => {
  jest.useFakeTimers();
  mockedList.mockReset();
  mockedSearch.mockReset();
});

afterEach(() => {
  jest.useRealTimers();
});

describe("BookList", () => {
  it("renders title, authors and year for each book", () => {
    render(<BookList initialData={initialData} />);
    expect(screen.getByText("Refactoring")).toBeInTheDocument();
    expect(screen.getByText("by Martin Fowler")).toBeInTheDocument();
    expect(screen.getByText("1999")).toBeInTheDocument();
  });

  it("does not fire any request before the debounce window elapses", () => {
    render(<BookList initialData={initialData} />);
    const input = screen.getByRole("searchbox");

    fireEvent.change(input, { target: { value: "c" } });
    fireEvent.change(input, { target: { value: "cl" } });
    fireEvent.change(input, { target: { value: "cle" } });

    act(() => {
      jest.advanceTimersByTime(200);
    });

    expect(mockedSearch).not.toHaveBeenCalled();
    expect(mockedList).not.toHaveBeenCalled();
  });

  it("fires a single search request after the debounce window", async () => {
    mockedSearch.mockResolvedValueOnce(makePage([makeBook({ id: "s-1", title: "Clean Code" })], 0, 1, false));

    render(<BookList initialData={initialData} />);
    const input = screen.getByRole("searchbox");

    fireEvent.change(input, { target: { value: "c" } });
    fireEvent.change(input, { target: { value: "cl" } });
    fireEvent.change(input, { target: { value: "clean" } });

    await act(async () => {
      jest.advanceTimersByTime(300);
    });

    expect(mockedSearch).toHaveBeenCalledTimes(1);
    expect(mockedSearch).toHaveBeenCalledWith({ title: "clean", limit: 20, offset: 0 });
    expect(mockedList).not.toHaveBeenCalled();
    expect(await screen.findByText("Clean Code")).toBeInTheDocument();
  });

  it("falls back to list (full catalog) when the search input is cleared", async () => {
    mockedSearch.mockResolvedValueOnce(makePage([makeBook({ id: "s-1", title: "Clean Code" })], 0, 1, false));
    mockedList.mockResolvedValueOnce(makePage([initialBook], 0, 1, false));

    render(<BookList initialData={initialData} />);
    const input = screen.getByRole("searchbox");

    fireEvent.change(input, { target: { value: "clean" } });
    await act(async () => {
      jest.advanceTimersByTime(300);
    });

    fireEvent.change(input, { target: { value: "" } });
    await act(async () => {
      jest.advanceTimersByTime(300);
    });

    expect(mockedList).toHaveBeenCalledTimes(1);
    expect(mockedList).toHaveBeenCalledWith({ limit: 20, offset: 0 });
  });

  it("shows the error alert when the API rejects", async () => {
    mockedSearch.mockRejectedValueOnce(new ApiError(503, "API is down"));

    render(<BookList initialData={initialData} />);
    const input = screen.getByRole("searchbox");
    fireEvent.change(input, { target: { value: "anything" } });

    await act(async () => {
      jest.advanceTimersByTime(300);
    });

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("API is down");
  });

  it("appends the next page when 'Load more' is clicked and uses the correct offset", async () => {
    const firstPageBooks = Array.from({ length: 20 }, (_, i) =>
      makeBook({ id: `b-${i}`, title: `Book ${i}` }),
    );
    const initialBigPage: PaginatedBooks = makePage(firstPageBooks, 0, 25, true);
    const secondPageBooks = Array.from({ length: 5 }, (_, i) =>
      makeBook({ id: `b-${i + 20}`, title: `Book ${i + 20}` }),
    );
    mockedList.mockResolvedValueOnce(makePage(secondPageBooks, 20, 25, false));

    render(<BookList initialData={initialBigPage} />);

    expect(screen.getByText("Book 0")).toBeInTheDocument();
    expect(screen.queryByText("Book 24")).not.toBeInTheDocument();

    const loadMore = screen.getByRole("button", { name: /load more/i });
    await act(async () => {
      fireEvent.click(loadMore);
    });

    expect(mockedList).toHaveBeenCalledTimes(1);
    expect(mockedList).toHaveBeenCalledWith({ limit: 20, offset: 20 });
    expect(await screen.findByText("Book 24")).toBeInTheDocument();
  });
});
