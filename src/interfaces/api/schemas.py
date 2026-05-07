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

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class AddBookRequest(BaseModel):
    """Request body for POST /api/v1/books."""

    title: str = Field(..., min_length=1, max_length=500, description="Book title")
    author: str = Field(..., min_length=1, max_length=300, description="Author name")
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

    @field_validator("title", "author")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field must not be blank.")
        return stripped


class UpdateBookStatusRequest(BaseModel):
    """Request body for PATCH /api/v1/books/{id}/status."""

    status: str = Field(
        ...,
        description="New reading status. Allowed values: unread, reading, read",
        pattern="^(unread|reading|read)$",
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class BookResponse(BaseModel):
    """Single book response envelope."""

    id: str
    title: str
    author: str
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
