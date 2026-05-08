"use client";

/**
 * BookCard Component
 * ==================
 * Displays a single book with status badge and action buttons.
 */

import type { Book, BookStatus } from "@/lib/api-client";

interface BookCardProps {
  book: Book;
  onDelete: (id: string) => Promise<void>;
  onStatusChange: (id: string, newStatus: BookStatus) => Promise<void>;
}

const NEXT_STATUS: Partial<Record<BookStatus, BookStatus>> = {
  unread: "reading",
  reading: "read",
};

const STATUS_LABEL: Record<BookStatus, string> = {
  unread: "Unread",
  reading: "Reading",
  read: "Read",
};

const STATUS_ACTIONS: Partial<Record<BookStatus, string>> = {
  unread: "Start Reading →",
  reading: "Mark as Read ✓",
};

export default function BookCard({ book, onDelete, onStatusChange }: BookCardProps): JSX.Element {
  const nextStatus = NEXT_STATUS[book.status];

  const handleStatusClick = (): void => {
    if (nextStatus) {
      void onStatusChange(book.id, nextStatus);
    }
  };

  const handleDeleteClick = (): void => {
    void onDelete(book.id);
  };

  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className={`badge badge-${book.status}`}>{STATUS_LABEL[book.status]}</span>
        {book.year_published && (
          <span className="text-muted text-sm">{book.year_published}</span>
        )}
      </div>

      {/* Title & Authors */}
      <div>
        <h3 style={{ fontWeight: 700, fontSize: "1rem", lineHeight: 1.3 }}>{book.title}</h3>
        <p className="text-muted text-sm" style={{ marginTop: "0.2rem" }}>
          by {book.authors.join(", ")}
        </p>
      </div>

      {/* ISBN & Genre */}
      <div className="flex items-center gap-2" style={{ flexWrap: "wrap" }}>
        <code className="text-muted text-sm" style={{ fontSize: "0.8rem" }}>
          ISBN {book.isbn}
        </code>
        <span className="badge" style={{ fontSize: "0.7rem" }}>
          {book.genre}
        </span>
      </div>

      {/* Actions */}
      <div className="flex gap-2" style={{ marginTop: "auto", paddingTop: "0.5rem" }}>
        {nextStatus && (
          <button
            onClick={handleStatusClick}
            className="btn btn-primary"
            style={{ flex: 1, fontSize: "0.8rem", padding: "0.4rem 0.75rem" }}
          >
            {STATUS_ACTIONS[book.status]}
          </button>
        )}
        <button
          onClick={handleDeleteClick}
          className="btn btn-ghost"
          style={{ fontSize: "0.8rem", padding: "0.4rem 0.75rem", color: "#dc2626" }}
          aria-label="Delete book"
          title="Remove from library"
        >
          🗑
        </button>
      </div>
    </div>
  );
}
