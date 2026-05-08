"use client";

/**
 * AddBookForm Component
 * =====================
 * Controlled form for submitting a new book to the API.
 * Performs client-side validation (required fields, ISBN format, year not in future)
 * before issuing the request. On success, redirects to the catalog so the
 * librarian can see the new book in the listing.
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

const CURRENT_YEAR = new Date().getFullYear();

function isValidIsbn(raw: string): boolean {
  const digits = raw.replace(/[-\s]/g, "");
  return /^\d{10}$/.test(digits) || /^\d{13}$/.test(digits);
}

function validate(form: FormState, currentYear: number): string[] {
  const errors: string[] = [];
  if (!form.title.trim()) errors.push("Title is required.");
  const authorsList = form.authors
    .split(",")
    .map((a) => a.trim())
    .filter((a) => a.length > 0);
  if (authorsList.length === 0) errors.push("At least one author is required.");
  if (!form.isbn.trim()) {
    errors.push("ISBN is required.");
  } else if (!isValidIsbn(form.isbn)) {
    errors.push("ISBN is not valid. Use 10 or 13 digits (hyphens optional).");
  }
  if (!form.genre.trim()) errors.push("Genre is required.");
  if (form.year_published.trim()) {
    const year = parseInt(form.year_published, 10);
    if (Number.isNaN(year)) {
      errors.push("Year published must be a number.");
    } else if (year > currentYear) {
      errors.push(`Year published cannot be in the future (max ${currentYear}).`);
    }
  }
  return errors;
}

export default function AddBookForm(): JSX.Element {
  const router = useRouter();
  const [form, setForm] = useState<FormState>(INITIAL_STATE);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [errors, setErrors] = useState<string[]>([]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ): void => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    const validationErrors = validate(form, CURRENT_YEAR);
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }

    setSubmitting(true);
    setErrors([]);

    const authorsList = form.authors
      .split(",")
      .map((a) => a.trim())
      .filter((a) => a.length > 0);

    try {
      await booksApi.add({
        title: form.title.trim(),
        authors: authorsList,
        isbn: form.isbn.trim(),
        genre: form.genre.trim(),
        year_published: form.year_published ? parseInt(form.year_published, 10) : null,
      });
      router.push("/catalog");
      router.refresh();
    } catch (err) {
      setErrors([
        err instanceof ApiError
          ? err.message
          : "An unexpected error occurred. Please try again.",
      ]);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={(e) => void handleSubmit(e)} noValidate>
      {errors.length > 0 && (
        <div className="alert alert-error" role="alert" data-testid="form-errors">
          {errors.length === 1 ? (
            errors[0]
          ) : (
            <ul style={{ margin: 0, paddingLeft: "1.25rem" }}>
              {errors.map((msg) => (
                <li key={msg}>{msg}</li>
              ))}
            </ul>
          )}
        </div>
      )}

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
          max={CURRENT_YEAR}
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
        <a href="/catalog" className="btn btn-ghost">
          Cancel
        </a>
      </div>
    </form>
  );
}
