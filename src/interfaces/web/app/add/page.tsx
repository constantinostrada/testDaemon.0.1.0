/**
 * Add Book page — /add
 * ====================
 * Client form for adding a new book to the library.
 */

import AddBookForm from "@/components/AddBookForm";

export default function AddBookPage(): JSX.Element {
  return (
    <div style={{ maxWidth: 600 }}>
      <div className="mt-2">
        <a href="/" className="btn btn-ghost text-sm">
          ← Back to library
        </a>
      </div>
      <h2 style={{ fontSize: "1.5rem", fontWeight: 700, margin: "1rem 0" }}>
        Add a New Book
      </h2>
      <div className="card">
        <AddBookForm />
      </div>
    </div>
  );
}
