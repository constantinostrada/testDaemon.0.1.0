/**
 * Home page — /
 * =============
 * Server component that fetches the book list and renders it.
 * Delegates display to the BookList client component.
 */

import type { PaginatedBooks } from "@/lib/api-client";
import BookList from "@/components/BookList";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function getBooks(): Promise<PaginatedBooks | null> {
  try {
    const res = await fetch(`${API_URL}/api/v1/books?limit=20`, {
      // Revalidate every 30 seconds (ISR)
      next: { revalidate: 30 },
    });
    if (!res.ok) return null;
    return res.json() as Promise<PaginatedBooks>;
  } catch {
    return null;
  }
}

export default async function HomePage(): Promise<JSX.Element> {
  const data = await getBooks();

  return (
    <div>
      <div className="flex items-center justify-between mt-2">
        <h2 style={{ fontSize: "1.5rem", fontWeight: 700 }}>My Library</h2>
        <a href="/add" className="btn btn-primary">
          + Add Book
        </a>
      </div>

      {data === null ? (
        <div className="alert alert-error mt-2">
          Could not connect to the API. Make sure the FastAPI server is running on{" "}
          <code>{API_URL}</code>.
        </div>
      ) : (
        <BookList initialData={data} />
      )}
    </div>
  );
}
