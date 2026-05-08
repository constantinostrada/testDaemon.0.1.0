# ADR 0001 — Catalogue search matching: substring vs exact

- **Status:** Accepted
- **Date:** 2026-05-07
- **Task:** BJWWdbaSpSMXLn0ffncS — *Búsqueda en el catálogo*
- **Deciders:** Library API team

## Context

The catalogue search feature accepts three optional, combinable criteria:
title keyword, author keyword, and publication year. The product brief
explicitly delegates the matching policy to engineering ("tomá la decisión
que mejor sirva al usuario final") but requires the choice to be:

- consistent across the system, and
- documented somewhere accessible to the team and to future agents.

Two reasonable options exist for textual fields (`title`, `author`):

1. **Exact match** — fast, predictable, but requires the user to know
   the precise title/author string. Effectively unusable for a real
   library UX.
2. **Case-insensitive substring** — friendlier ("clean" finds *Clean
   Code*; "martin" finds *Robert C. Martin*), at the cost of a linear
   scan of the catalogue. Acceptable at this stage (in-memory repository,
   small catalogues; can be revisited if/when we move to a SQL or
   full-text store).

For `year_published` the choice is simpler: a year is a precise integer.
Substring matching on a 4-digit number ("199" matching every book from
1990–1999) would surprise users and conflicts with the "exact year"
reading of the spec.

## Decision

The catalogue search uses the following matching rules:

| Criterion        | Rule                                              |
| ---------------- | ------------------------------------------------- |
| `title`          | Case-insensitive **substring** match on the title |
| `author`         | Case-insensitive **substring** match on **any** of the book's authors |
| `year_published` | **Exact** integer match                           |

Multiple criteria are combined with **AND** semantics: a book must
satisfy every supplied criterion to be returned. Missing criteria are
ignored. An empty result set is a normal outcome and is returned as
HTTP `200` with `total: 0` — never an error.

Whitespace-only textual criteria are treated as "no criterion".

## Consequences

- **UX:** Users can find books without knowing exact titles or full
  author names — the common library-search expectation.
- **Performance:** O(n) over the in-memory catalogue. Fine at current
  scale; the `BookRepository.search` interface returns `(books, total)`
  so a future implementation can push the work to the storage backend
  without changing callers.
- **Consistency:** The rules are the contract of `BookRepository.search`
  (domain), enforced in `InMemoryBookRepository.search` (infrastructure),
  preserved by `SearchBooksUseCase` (application), and surfaced verbatim
  in the OpenAPI description of `GET /api/v1/books/search` (interfaces).
  Any future repository implementation must honour these same rules.

## Where this decision is recorded

Per the task's "documentado en algún lugar accesible al equipo"
acceptance criterion, this decision is recorded in three accessible
places so it cannot be lost:

1. This ADR (`docs/decisions/0001-search-matching.md`).
2. The `SearchBooksUseCase` class docstring
   (`src/application/use_cases/search_books.py`).
3. The OpenAPI `description` field of `GET /api/v1/books/search`
   (`src/interfaces/api/controllers/book_controller.py`), which is also
   visible at runtime via the `/docs` endpoint.
