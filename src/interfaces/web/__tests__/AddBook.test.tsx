/**
 * AddBook screen tests
 * ====================
 * Validates the 6 ACs of "Pantalla para sumar libros":
 *   1. link-from-catalog          : evident path from /catalog to the form
 *   2. load-all-data              : every book field is captured by the form
 *   3. client-validation-blocks   : invalid input (bad ISBN, future year, empty)
 *                                   surfaces inline errors before any API call
 *   4. api-error-shown            : when the API rejects, the reason is visible
 *   5. redirect-and-visible       : on success the user lands on /catalog
 *   6. cancel-returns             : Cancel navigates back to /catalog without saving
 */

import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AddBookForm from "@/components/AddBookForm";
import CatalogPage from "@/app/catalog/page";
import { booksApi, ApiError, type Book } from "@/lib/api-client";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const pushMock = jest.fn();
const refreshMock = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: pushMock,
    refresh: refreshMock,
    back: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
}));

jest.mock("@/lib/api-client", () => {
  const actual = jest.requireActual("@/lib/api-client");
  return {
    ...actual,
    booksApi: {
      add: jest.fn(),
      list: jest.fn(),
      search: jest.fn(),
      getById: jest.fn(),
      updateStatus: jest.fn(),
      delete: jest.fn(),
    },
  };
});

const mockedBooksApi = booksApi as jest.Mocked<typeof booksApi>;

// ---------------------------------------------------------------------------
// IntersectionObserver polyfill (CatalogPage uses it for infinite scroll)
// ---------------------------------------------------------------------------

class NoopIntersectionObserver implements IntersectionObserver {
  readonly root: Element | Document | null = null;
  readonly rootMargin: string = "";
  readonly thresholds: ReadonlyArray<number> = [];
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }
}

beforeAll(() => {
  (global as unknown as { IntersectionObserver: unknown }).IntersectionObserver =
    NoopIntersectionObserver;
});

beforeEach(() => {
  pushMock.mockReset();
  refreshMock.mockReset();
  mockedBooksApi.add.mockReset();
  mockedBooksApi.list.mockReset();
  mockedBooksApi.search.mockReset();
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeBook(overrides: Partial<Book> = {}): Book {
  return {
    id: "id-" + Math.random().toString(36).slice(2, 8),
    title: "Untitled",
    authors: ["Anon"],
    isbn: "9780132350884",
    genre: "General",
    status: "unread",
    year_published: 2020,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
    ...overrides,
  };
}

async function fillValidForm(user: ReturnType<typeof userEvent.setup>): Promise<void> {
  await user.type(screen.getByLabelText(/^title/i), "Clean Code");
  await user.type(screen.getByLabelText(/^authors/i), "Robert C. Martin");
  await user.type(screen.getByLabelText(/^isbn/i), "978-0-13-235088-4");
  await user.type(screen.getByLabelText(/^genre/i), "Software");
  await user.type(screen.getByLabelText(/year published/i), "2008");
}

// ---------------------------------------------------------------------------
// AC1 — link-from-catalog
// ---------------------------------------------------------------------------

describe("AC: link-from-catalog", () => {
  it("AC1: catalog page exposes an evident link to the add-book form", async () => {
    mockedBooksApi.list.mockResolvedValue({
      books: [],
      total: 0,
      limit: 20,
      offset: 0,
      has_more: false,
    });

    render(<CatalogPage />);

    const link = await screen.findByTestId("catalog-add-book-link");
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "/add");
    expect(link).toHaveTextContent(/add book/i);
  });
});

// ---------------------------------------------------------------------------
// AC2 — load-all-data
// ---------------------------------------------------------------------------

describe("AC: load-all-data", () => {
  it("AC2: form captures title, authors, isbn, genre and year_published", async () => {
    mockedBooksApi.add.mockResolvedValue(makeBook());
    const user = userEvent.setup();

    render(<AddBookForm />);

    await user.type(screen.getByLabelText(/^title/i), "The Pragmatic Programmer");
    await user.type(screen.getByLabelText(/^authors/i), "David Thomas, Andrew Hunt");
    await user.type(screen.getByLabelText(/^isbn/i), "9780201616224");
    await user.type(screen.getByLabelText(/^genre/i), "Software");
    await user.type(screen.getByLabelText(/year published/i), "1999");

    await user.click(screen.getByRole("button", { name: /add to library/i }));

    await waitFor(() => expect(mockedBooksApi.add).toHaveBeenCalledTimes(1));
    expect(mockedBooksApi.add).toHaveBeenCalledWith({
      title: "The Pragmatic Programmer",
      authors: ["David Thomas", "Andrew Hunt"],
      isbn: "9780201616224",
      genre: "Software",
      year_published: 1999,
    });
  });
});

// ---------------------------------------------------------------------------
// AC3 — client-validation-blocks
// ---------------------------------------------------------------------------

describe("AC: client-validation-blocks", () => {
  it("AC3a: empty required fields surface inline errors before any API call", async () => {
    const user = userEvent.setup();
    render(<AddBookForm />);

    await user.click(screen.getByRole("button", { name: /add to library/i }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/title is required/i);
    expect(alert).toHaveTextContent(/author/i);
    expect(alert).toHaveTextContent(/isbn is required/i);
    expect(alert).toHaveTextContent(/genre is required/i);
    expect(mockedBooksApi.add).not.toHaveBeenCalled();
  });

  it("AC3b: malformed ISBN is rejected client-side before any API call", async () => {
    const user = userEvent.setup();
    render(<AddBookForm />);

    await user.type(screen.getByLabelText(/^title/i), "Clean Code");
    await user.type(screen.getByLabelText(/^authors/i), "Robert C. Martin");
    await user.type(screen.getByLabelText(/^isbn/i), "not-a-real-isbn");
    await user.type(screen.getByLabelText(/^genre/i), "Software");

    await user.click(screen.getByRole("button", { name: /add to library/i }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/isbn is not valid/i);
    expect(mockedBooksApi.add).not.toHaveBeenCalled();
  });

  it("AC3c: future year_published is rejected client-side before any API call", async () => {
    const user = userEvent.setup();
    render(<AddBookForm />);

    await user.type(screen.getByLabelText(/^title/i), "Clean Code");
    await user.type(screen.getByLabelText(/^authors/i), "Robert C. Martin");
    await user.type(screen.getByLabelText(/^isbn/i), "9780132350884");
    await user.type(screen.getByLabelText(/^genre/i), "Software");

    const futureYear = String(new Date().getFullYear() + 5);
    await user.type(screen.getByLabelText(/year published/i), futureYear);

    await user.click(screen.getByRole("button", { name: /add to library/i }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/cannot be in the future/i);
    expect(mockedBooksApi.add).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// AC4 — api-error-shown
// ---------------------------------------------------------------------------

describe("AC: api-error-shown", () => {
  it("AC4: when the API rejects, the rejection reason is shown to the user", async () => {
    mockedBooksApi.add.mockRejectedValueOnce(
      new ApiError(409, "A book with this ISBN already exists"),
    );
    const user = userEvent.setup();

    render(<AddBookForm />);
    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: /add to library/i }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/already exists/i);
    expect(pushMock).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// AC5 — redirect-and-visible
// ---------------------------------------------------------------------------

describe("AC: redirect-and-visible", () => {
  it("AC5: after a successful save, the user is sent back to /catalog", async () => {
    mockedBooksApi.add.mockResolvedValueOnce(
      makeBook({ id: "new-1", title: "Clean Code" }),
    );
    const user = userEvent.setup();

    render(<AddBookForm />);
    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: /add to library/i }));

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/catalog"));
    expect(refreshMock).toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// AC6 — cancel-returns
// ---------------------------------------------------------------------------

describe("AC: cancel-returns", () => {
  it("AC6: Cancel link goes to /catalog and no API call is made", async () => {
    render(<AddBookForm />);

    const cancel = screen.getByRole("link", { name: /cancel/i });
    expect(cancel).toHaveAttribute("href", "/catalog");

    // Sanity check: nothing was submitted.
    await act(async () => {});
    expect(mockedBooksApi.add).not.toHaveBeenCalled();
    expect(pushMock).not.toHaveBeenCalled();
  });
});
