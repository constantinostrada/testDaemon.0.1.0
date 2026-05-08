"""
Acceptance tests for the catalogue model (task: "Modelo del catálogo").

These tests map directly to the prose acceptance criteria of the task:
  - A book can be created and retrieved.
  - Invalid ISBNs are rejected with a clear error message.
  - Two books with the same ISBN cannot be loaded.
  - The full catalogue listing can be obtained.

They exercise the API end-to-end against the in-memory repository.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.interfaces.api.dependencies import _book_repository_singleton
from src.interfaces.api.main import create_app


@pytest.fixture()
async def client() -> AsyncIterator[AsyncClient]:
    _book_repository_singleton.cache_clear()
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        async with app.router.lifespan_context(app):
            yield ac
    _book_repository_singleton.cache_clear()


CLEAN_CODE = {
    "title": "Clean Code",
    "authors": ["Robert C. Martin"],
    "isbn": "9780132350884",
    "genre": "Software Engineering",
    "year_published": 2008,
}

DESIGN_PATTERNS = {
    "title": "Design Patterns",
    "authors": ["Erich Gamma", "Richard Helm", "Ralph Johnson", "John Vlissides"],
    "isbn": "9780201633610",
    "genre": "Software Engineering",
    "year_published": 1994,
}


class TestCatalogAcceptance:
    async def test_create_and_retrieve_book(self, client: AsyncClient) -> None:
        """AC: a book can be created and then retrieved."""
        created = await client.post("/api/v1/books", json=CLEAN_CODE)
        assert created.status_code == 201
        book_id = created.json()["id"]

        fetched = await client.get(f"/api/v1/books/{book_id}")
        assert fetched.status_code == 200
        body = fetched.json()
        assert body["title"] == CLEAN_CODE["title"]
        assert body["authors"] == CLEAN_CODE["authors"]
        assert body["isbn"] == CLEAN_CODE["isbn"]
        assert body["genre"] == CLEAN_CODE["genre"]
        assert body["year_published"] == CLEAN_CODE["year_published"]

    async def test_invalid_isbn_rejected_with_clear_message(
        self, client: AsyncClient
    ) -> None:
        """AC: invalid ISBNs are rejected with a clear error message."""
        payload = {**CLEAN_CODE, "isbn": "1234567890"}  # bad check digit
        response = await client.post("/api/v1/books", json=payload)
        assert response.status_code == 422
        body = response.json()
        # Error envelope uses FastAPI's default `detail` field.
        detail = str(body.get("detail", "")).lower()
        assert "isbn" in detail

    async def test_duplicate_isbn_rejected(self, client: AsyncClient) -> None:
        """AC: cannot load two books with the same ISBN."""
        first = await client.post("/api/v1/books", json=CLEAN_CODE)
        assert first.status_code == 201

        # Same ISBN but different title/authors — must still be refused.
        duplicate_payload = {
            **CLEAN_CODE,
            "title": "Another Title",
            "authors": ["Someone Else"],
        }
        second = await client.post("/api/v1/books", json=duplicate_payload)
        assert second.status_code == 409
        detail = str(second.json().get("detail", "")).lower()
        assert "isbn" in detail or "duplicate" in detail

    async def test_list_full_catalogue(self, client: AsyncClient) -> None:
        """AC: the full catalogue listing can be obtained."""
        await client.post("/api/v1/books", json=CLEAN_CODE)
        await client.post("/api/v1/books", json=DESIGN_PATTERNS)

        response = await client.get("/api/v1/books")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

        isbns = {b["isbn"] for b in data["books"]}
        assert isbns == {CLEAN_CODE["isbn"], DESIGN_PATTERNS["isbn"]}

        # Multi-author entry preserves all authors in order.
        dp = next(b for b in data["books"] if b["isbn"] == DESIGN_PATTERNS["isbn"])
        assert dp["authors"] == DESIGN_PATTERNS["authors"]

    async def test_supports_one_or_more_authors(self, client: AsyncClient) -> None:
        """Spec wording: 'uno o más autores' — both shapes must be accepted."""
        # Single author
        single = await client.post("/api/v1/books", json=CLEAN_CODE)
        assert single.status_code == 201
        assert single.json()["authors"] == ["Robert C. Martin"]

        # Multiple authors
        multi = await client.post("/api/v1/books", json=DESIGN_PATTERNS)
        assert multi.status_code == 201
        assert multi.json()["authors"] == DESIGN_PATTERNS["authors"]

    async def test_delete_book_removes_from_catalogue(
        self, client: AsyncClient
    ) -> None:
        """AC: a book can be deleted and is then absent from the catalogue."""
        created = await client.post("/api/v1/books", json=CLEAN_CODE)
        assert created.status_code == 201
        book_id = created.json()["id"]

        deleted = await client.delete(f"/api/v1/books/{book_id}")
        assert deleted.status_code == 204

        fetched = await client.get(f"/api/v1/books/{book_id}")
        assert fetched.status_code == 404

        listing = await client.get("/api/v1/books")
        assert listing.status_code == 200
        ids_in_listing = {b["id"] for b in listing.json()["books"]}
        assert book_id not in ids_in_listing

    async def test_get_nonexistent_book_returns_404_with_clear_error(
        self, client: AsyncClient
    ) -> None:
        """AC: requesting a book that does not exist returns 404 with detail."""
        # Well-formed UUID that has never been created.
        missing_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/v1/books/{missing_id}")
        assert response.status_code == 404
        body = response.json()
        detail = str(body.get("detail", "")).lower()
        assert detail  # non-empty, human-readable message
        assert "book" in detail or "not found" in detail or missing_id in detail


# ---------------------------------------------------------------------------
# Search acceptance tests (task: "Búsqueda en el catálogo")
#
# Maps to the prose acceptance criteria:
#   - Search by word in title returns matching books.
#   - Search by author returns matching books.
#   - Search by year returns matching books.
#   - Combining criteria applies AND.
#   - No matches → valid empty response (not an error).
#   - Decision substring-vs-exact is documented in an accessible place.
# ---------------------------------------------------------------------------


class TestCatalogSearchAcceptance:
    async def _seed(self, client: AsyncClient) -> None:
        for payload in (CLEAN_CODE, DESIGN_PATTERNS):
            r = await client.post("/api/v1/books", json=payload)
            assert r.status_code == 201

    async def test_search_by_title_keyword(self, client: AsyncClient) -> None:
        """AC: a keyword in the title returns the matching books."""
        await self._seed(client)

        # Case-insensitive substring: "clean" must find "Clean Code".
        response = await client.get("/api/v1/books/search", params={"title": "clean"})
        assert response.status_code == 200
        data = response.json()
        isbns = {b["isbn"] for b in data["books"]}
        assert CLEAN_CODE["isbn"] in isbns
        assert DESIGN_PATTERNS["isbn"] not in isbns
        assert data["total"] == 1

    async def test_search_by_author(self, client: AsyncClient) -> None:
        """AC: a search by author returns the matching books."""
        await self._seed(client)

        # Match a single author of a multi-author book.
        response = await client.get(
            "/api/v1/books/search", params={"author": "Gamma"}
        )
        assert response.status_code == 200
        data = response.json()
        isbns = {b["isbn"] for b in data["books"]}
        assert isbns == {DESIGN_PATTERNS["isbn"]}
        assert data["total"] == 1

        # And case-insensitive substring on a single-author book.
        response = await client.get(
            "/api/v1/books/search", params={"author": "martin"}
        )
        assert response.status_code == 200
        data = response.json()
        isbns = {b["isbn"] for b in data["books"]}
        assert isbns == {CLEAN_CODE["isbn"]}

    async def test_search_by_year(self, client: AsyncClient) -> None:
        """AC: a search by year returns the matching books."""
        await self._seed(client)

        response = await client.get("/api/v1/books/search", params={"year": 2008})
        assert response.status_code == 200
        data = response.json()
        isbns = {b["isbn"] for b in data["books"]}
        assert isbns == {CLEAN_CODE["isbn"]}
        assert data["total"] == 1

    async def test_search_combines_criteria_with_and(
        self, client: AsyncClient
    ) -> None:
        """AC: combining criteria applies AND — all of them must match."""
        await self._seed(client)

        # Title AND author both match Clean Code → 1 result.
        response = await client.get(
            "/api/v1/books/search",
            params={"title": "code", "author": "Martin"},
        )
        assert response.status_code == 200
        data = response.json()
        isbns = {b["isbn"] for b in data["books"]}
        assert isbns == {CLEAN_CODE["isbn"]}

        # Title matches Clean Code but year is wrong → 0 results.
        response = await client.get(
            "/api/v1/books/search",
            params={"title": "clean", "year": 1994},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["books"] == []

    async def test_search_with_no_matches_returns_valid_empty_response(
        self, client: AsyncClient
    ) -> None:
        """AC: when nothing matches, the response is a valid empty list (not an error)."""
        await self._seed(client)

        response = await client.get(
            "/api/v1/books/search", params={"title": "definitely-not-in-any-title"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["books"] == []
        assert data["total"] == 0
        assert data["has_more"] is False

    async def test_search_decision_is_documented_and_discoverable(self) -> None:
        """AC: the substring-vs-exact decision is documented somewhere accessible.

        The decision must be discoverable by the team. We assert it is recorded
        in the ADR file, and that BOTH textual rules ('substring' for title and
        author) and the year rule ('exact') are explicitly stated.
        """
        from pathlib import Path

        adr_path = (
            Path(__file__).resolve().parents[2]
            / "docs"
            / "decisions"
            / "0001-search-matching.md"
        )
        assert adr_path.exists(), f"Expected ADR at {adr_path}"
        text = adr_path.read_text(encoding="utf-8").lower()
        assert "substring" in text
        assert "exact" in text
        assert "title" in text
        assert "author" in text
        assert "year" in text
