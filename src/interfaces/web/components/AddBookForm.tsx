"use client";

/**
 * AddBookForm Component
 * =====================
 * Controlled form for submitting a new book to the API.
 * On success, redirects to the home page.
 */

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { booksApi, ApiError } from "@/lib/api-client";

interface FormState {
  title: string;
  author: string;
  isbn: string;
  year_published: string;
  description: string;
}

const INITIAL_STATE: FormState = {
  title: "",
  author: "",
  isbn: "",
  year_published: "",
  description: "",
};

export default function AddBookForm(): JSX.Element {
  const router = useRouter();
  const [form, setForm] = useState<FormState>(INITIAL_STATE);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ): void => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await booksApi.add({
        title: form.title.trim(),
        author: form.author.trim(),
        isbn: form.isbn.trim(),
        year_published: form.year_published ? parseInt(form.year_published, 10) : null,
        description: form.description.trim() || null,
      });
      router.push("/");
      router.refresh();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "An unexpected error occurred. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={(e) => void handleSubmit(e)} noValidate>
      {error && <div className="alert alert-error">{error}</div>}

      <div className="form-group">
        <label htmlFor="title" className="form-label">
          Title <span style={{ color: "#dc2626" }}>*</span>
        </label>
        <input
          id="title"
          name="title"
          type="text"
          className="form-input"
          value={form.title}
          onChange={handleChange}
          required
          maxLength={500}
          placeholder="e.g. The Pragmatic Programmer"
          disabled={submitting}
        />
      </div>

      <div className="form-group">
        <label htmlFor="author" className="form-label">
          Author <span style={{ color: "#dc2626" }}>*</span>
        </label>
        <input
          id="author"
          name="author"
          type="text"
          className="form-input"
          value={form.author}
          onChange={handleChange}
          required
          maxLength={300}
          placeholder="e.g. David Thomas, Andrew Hunt"
          disabled={submitting}
        />
      </div>

      <div className="form-group">
        <label htmlFor="isbn" className="form-label">
          ISBN <span style={{ color: "#dc2626" }}>*</span>
        </label>
        <input
          id="isbn"
          name="isbn"
          type="text"
          className="form-input"
          value={form.isbn}
          onChange={handleChange}
          required
          maxLength={17}
          placeholder="e.g. 978-0-13-468599-1"
          disabled={submitting}
        />
        <span className="text-muted text-sm">ISBN-10 or ISBN-13, hyphens optional</span>
      </div>

      <div className="form-group">
        <label htmlFor="year_published" className="form-label">
          Year Published
        </label>
        <input
          id="year_published"
          name="year_published"
          type="number"
          className="form-input"
          value={form.year_published}
          onChange={handleChange}
          min={1000}
          max={2100}
          placeholder="e.g. 2019"
          disabled={submitting}
        />
      </div>

      <div className="form-group">
        <label htmlFor="description" className="form-label">
          Description
        </label>
        <textarea
          id="description"
          name="description"
          className="form-textarea"
          value={form.description}
          onChange={handleChange}
          maxLength={2000}
          placeholder="Short synopsis or notes…"
          disabled={submitting}
        />
      </div>

      <div className="flex gap-2" style={{ marginTop: "1.5rem" }}>
        <button
          type="submit"
          className="btn btn-primary"
          disabled={submitting}
          style={{ flex: 1 }}
        >
          {submitting ? "Adding…" : "Add to Library"}
        </button>
        <a href="/" className="btn btn-ghost">
          Cancel
        </a>
      </div>
    </form>
  );
}
