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
  authors: string;
  isbn: string;
  genre: string;
  year_published: string;
}

const INITIAL_STATE: FormState = {
  title: "",
  authors: "",
  isbn: "",
  genre: "",
  year_published: "",
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

    const authorsList = form.authors
      .split(",")
      .map((a) => a.trim())
      .filter((a) => a.length > 0);

    if (authorsList.length === 0) {
      setError("At least one author is required.");
      setSubmitting(false);
      return;
    }

    try {
      await booksApi.add({
        title: form.title.trim(),
        authors: authorsList,
        isbn: form.isbn.trim(),
        genre: form.genre.trim(),
        year_published: form.year_published ? parseInt(form.year_published, 10) : null,
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
        <label htmlFor="authors" className="form-label">
          Authors <span style={{ color: "#dc2626" }}>*</span>
        </label>
        <input
          id="authors"
          name="authors"
          type="text"
          className="form-input"
          value={form.authors}
          onChange={handleChange}
          required
          maxLength={300}
          placeholder="e.g. David Thomas, Andrew Hunt"
          disabled={submitting}
        />
        <span className="text-muted text-sm">Separate multiple authors with commas</span>
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
        <label htmlFor="genre" className="form-label">
          Genre <span style={{ color: "#dc2626" }}>*</span>
        </label>
        <input
          id="genre"
          name="genre"
          type="text"
          className="form-input"
          value={form.genre}
          onChange={handleChange}
          required
          maxLength={100}
          placeholder="e.g. Software"
          disabled={submitting}
        />
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
