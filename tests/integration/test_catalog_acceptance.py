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
