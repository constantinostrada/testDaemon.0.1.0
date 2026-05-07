"""
Integration tests for the /api/v1/books endpoints.

Uses FastAPI's TestClient against the real in-memory repository wired
through `dependencies.py`. The repository singleton is reset between
tests so each case gets a clean catalogue.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.interfaces.api.dependencies import _book_repository_singleton
from src.interfaces.api.main import create_app


@pytest.fixture()
async def client() -> AsyncIterator[AsyncClient]:
    """Spin up a test app with a fresh in-memory book repository."""
    _book_repository_singleton.cache_clear()

    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        async with app.router.lifespan_context(app):
            yield ac

    _book_repository_singleton.cache_clear()


VALID_BOOK_PAYLOAD = {
    "title": "The Pragmatic Programmer",
    "authors": ["David Thomas", "Andrew Hunt"],
    "isbn": "9780135957059",
    "genre": "Software Engineering",
    "year_published": 2019,
}


class TestHealthEndpoint:
    async def test_health_returns_ok(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestAddBook:
    async def test_add_book_returns_201(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/books", json=VALID_BOOK_PAYLOAD)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == VALID_BOOK_PAYLOAD["title"]
        assert data["authors"] == VALID_BOOK_PAYLOAD["authors"]
        assert data["genre"] == VALID_BOOK_PAYLOAD["genre"]
        assert data["status"] == "unread"
        assert "id" in data

    async def test_add_duplicate_isbn_returns_409(self, client: AsyncClient) -> None:
        await client.post("/api/v1/books", json=VALID_BOOK_PAYLOAD)
        response = await client.post("/api/v1/books", json=VALID_BOOK_PAYLOAD)
        assert response.status_code == 409

    async def test_add_invalid_isbn_returns_422(self, client: AsyncClient) -> None:
        payload = {**VALID_BOOK_PAYLOAD, "isbn": "1234567890"}
        response = await client.post("/api/v1/books", json=payload)
        assert response.status_code == 422


class TestListBooks:
    async def test_list_returns_empty_initially(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/books")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["books"] == []

    async def test_list_returns_added_books(self, client: AsyncClient) -> None:
        await client.post("/api/v1/books", json=VALID_BOOK_PAYLOAD)
        response = await client.get("/api/v1/books")
        assert response.status_code == 200
        assert response.json()["total"] == 1

    async def test_filter_by_status(self, client: AsyncClient) -> None:
        await client.post("/api/v1/books", json=VALID_BOOK_PAYLOAD)
        response = await client.get("/api/v1/books?status_filter=reading")
        assert response.status_code == 200
        assert response.json()["total"] == 0


class TestGetBook:
    async def test_get_existing_book(self, client: AsyncClient) -> None:
        add = await client.post("/api/v1/books", json=VALID_BOOK_PAYLOAD)
        book_id = add.json()["id"]
        response = await client.get(f"/api/v1/books/{book_id}")
        assert response.status_code == 200
        assert response.json()["id"] == book_id

    async def test_get_nonexistent_returns_404(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/books/does-not-exist")
        assert response.status_code == 404


class TestUpdateBookStatus:
    async def test_update_status_reading(self, client: AsyncClient) -> None:
        add = await client.post("/api/v1/books", json=VALID_BOOK_PAYLOAD)
        book_id = add.json()["id"]
        response = await client.patch(
            f"/api/v1/books/{book_id}/status", json={"status": "reading"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "reading"

    async def test_invalid_transition_returns_422(self, client: AsyncClient) -> None:
        add = await client.post("/api/v1/books", json=VALID_BOOK_PAYLOAD)
        book_id = add.json()["id"]
        # Unread → Read is forbidden
        response = await client.patch(
            f"/api/v1/books/{book_id}/status", json={"status": "read"}
        )
        assert response.status_code == 422


class TestDeleteBook:
    async def test_delete_existing_book(self, client: AsyncClient) -> None:
        add = await client.post("/api/v1/books", json=VALID_BOOK_PAYLOAD)
        book_id = add.json()["id"]
        response = await client.delete(f"/api/v1/books/{book_id}")
        assert response.status_code == 204

    async def test_delete_nonexistent_returns_404(self, client: AsyncClient) -> None:
        response = await client.delete("/api/v1/books/ghost-id")
        assert response.status_code == 404
