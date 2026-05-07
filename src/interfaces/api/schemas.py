"""
API Request / Response Schemas
================================
Pydantic models used exclusively in the HTTP layer for:
  - Input validation (request bodies / query params)
  - Response serialisation

These are NOT application DTOs — they are HTTP-layer contracts.
The controllers map these ↔ application DTOs.

Rules (interfaces layer):
  - Pydantic imports are allowed here.
  - No domain entities, no infrastructure imports.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Author request schemas
# ---------------------------------------------------------------------------


class CreateAuthorRequest(BaseModel):
    """Request body for POST /api/v1/authors."""

    full_name: str = Field(
        ..., min_length=1, max_length=300, description="Author's full name"
    )
    bio: str | None = Field(
        default=None, max_length=2000, description="Optional biography"
    )
    date_of_birth: date | None = Field(
        default=None, description="Optional date of birth (ISO format)"
    )

    @field_validator("full_name")
    @classmethod
    def strip_full_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("full_name must not be blank.")
        return stripped


class UpdateAuthorRequest(BaseModel):
    """Request body for PATCH /api/v1/authors/{id}."""

    full_name: str | None = Field(
        default=None, min_length=1, max_length=300
    )
    bio: str | None = Field(default=None, max_length=2000)
    date_of_birth: date | None = Field(default=None)


# ---------------------------------------------------------------------------
# Book request schemas
# ---------------------------------------------------------------------------


class AddBookRequest(BaseModel):
    """Request body for POST /api/v1/books."""

    title: str = Field(..., min_length=1, max_length=500, description="Book title")
    author_ids: list[str] = Field(
        ...,
        min_length=1,
        description="IDs of one or more existing authors (must be non-empty).",
    )
    isbn: str = Field(
        ...,
        min_length=10,
        max_length=17,
        description="ISBN-10 or ISBN-13 (hyphens optional)",
    )
    year_published: int | None = Field(
        default=None, ge=1000, le=2100, description="Publication year"
    )
    description: str | None = Field(
        default=None, max_length=2000, description="Short description or synopsis"
    )

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("title must not be blank.")
        return stripped


class UpdateBookRequest(BaseModel):
    """Request body for PATCH /api/v1/books/{id} — mutable metadata."""

    title: str | None = Field(default=None, min_length=1, max_length=500)
    author_ids: list[str] | None = Field(
        default=None,
        min_length=1,
        description="If provided, replaces the book's author list.",
    )
    year_published: int | None = Field(default=None, ge=1000, le=2100)
    description: str | None = Field(default=None, max_length=2000)


class UpdateBookStatusRequest(BaseModel):
    """Request body for PATCH /api/v1/books/{id}/status."""

    status: str = Field(
        ...,
        description="New reading status. Allowed values: unread, reading, read",
        pattern="^(unread|reading|read)$",
    )


# ---------------------------------------------------------------------------
# Author response schemas
# ---------------------------------------------------------------------------


class AuthorResponse(BaseModel):
    """Single author response envelope."""

    id: str
    full_name: str
    bio: str | None
    date_of_birth: date | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedAuthorsResponse(BaseModel):
    """Paginated list of authors."""

    authors: list[AuthorResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


# ---------------------------------------------------------------------------
# Book response schemas
# ---------------------------------------------------------------------------


class BookResponse(BaseModel):
    """Single book response envelope (with hydrated authors)."""

    id: str
    title: str
    authors: list[AuthorResponse]
    isbn: str
    status: str
    year_published: int | None
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedBooksResponse(BaseModel):
    """Paginated list of books."""

    books: list[BookResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


# ---------------------------------------------------------------------------
# Misc schemas
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    """Health-check response."""

    status: str
    version: str
    environment: str


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    error: str
    detail: str | None = None
    code: str | None = None
