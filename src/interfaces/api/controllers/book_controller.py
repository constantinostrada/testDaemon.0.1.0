"""
BookController — FastAPI Router
================================
HTTP entry point for all /api/v1/books routes.

Pattern:
  1. Validate HTTP input (Pydantic schemas handle this automatically).
  2. Map HTTP schema → application DTO.
  3. Invoke use case.
  4. Map DTO → HTTP response schema.
  5. Return with the correct HTTP status code.

Rules (interfaces layer):
  - No business logic.
  - No direct repository calls.
  - No raw domain entity manipulation.
  - HTTP status codes are decided here, based on application exceptions.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.application.dtos.book_dtos import (
    AddBookInputDTO,
    DeleteBookInputDTO,
    GetBookInputDTO,
    ListBooksInputDTO,
    UpdateBookStatusInputDTO,
)
from src.application.use_cases.add_book import AddBookUseCase
from src.application.use_cases.delete_book import DeleteBookUseCase
from src.application.use_cases.get_book import GetBookUseCase
from src.application.use_cases.list_books import ListBooksUseCase
from src.application.use_cases.update_book_status import UpdateBookStatusUseCase
from src.domain.exceptions.domain_exceptions import (
    BookNotFoundError,
    DuplicateBookError,
    InvalidBookStatusTransitionError,
    InvalidISBNError,
)
from src.interfaces.api.dependencies import (
    provide_add_book_use_case,
    provide_delete_book_use_case,
    provide_get_book_use_case,
    provide_list_books_use_case,
    provide_update_book_status_use_case,
)
from src.interfaces.api.schemas import (
    AddBookRequest,
    BookResponse,
    PaginatedBooksResponse,
    UpdateBookStatusRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/books", tags=["Books"])


# ---------------------------------------------------------------------------
# POST /api/v1/books — Add a book
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new book",
    description="Add a book to the library catalogue. ISBN must be valid and unique.",
)
async def add_book(
    body: AddBookRequest,
    use_case: Annotated[AddBookUseCase, Depends(provide_add_book_use_case)],
) -> BookResponse:
    try:
        dto = AddBookInputDTO(
            title=body.title,
            author=body.author,
            isbn=body.isbn,
            year_published=body.year_published,
            description=body.description,
        )
        result = await use_case.execute(dto)
        return BookResponse(**result.__dict__)
    except InvalidISBNError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        ) from exc
    except DuplicateBookError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc


# ---------------------------------------------------------------------------
# GET /api/v1/books — List books
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=PaginatedBooksResponse,
    status_code=status.HTTP_200_OK,
    summary="List all books",
    description="Return a paginated list of books, optionally filtered by status.",
)
async def list_books(
    use_case: Annotated[ListBooksUseCase, Depends(provide_list_books_use_case)],
    status_filter: Annotated[
        str | None,
        Query(description="Filter by reading status: unread | reading | read"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=200, description="Page size")] = 50,
    offset: Annotated[int, Query(ge=0, description="Page offset")] = 0,
) -> PaginatedBooksResponse:
    try:
        dto = ListBooksInputDTO(
            status_filter=status_filter,
            limit=limit,
            offset=offset,
        )
        result = await use_case.execute(dto)
        return PaginatedBooksResponse(
            books=[BookResponse(**b.__dict__) for b in result.books],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
            has_more=result.has_more,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# GET /api/v1/books/{book_id} — Get a single book
# ---------------------------------------------------------------------------


@router.get(
    "/{book_id}",
    response_model=BookResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a book by ID",
)
async def get_book(
    book_id: str,
    use_case: Annotated[GetBookUseCase, Depends(provide_get_book_use_case)],
) -> BookResponse:
    try:
        dto = GetBookInputDTO(book_id=book_id)
        result = await use_case.execute(dto)
        return BookResponse(**result.__dict__)
    except BookNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc


# ---------------------------------------------------------------------------
# PATCH /api/v1/books/{book_id}/status — Update reading status
# ---------------------------------------------------------------------------


@router.patch(
    "/{book_id}/status",
    response_model=BookResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a book's reading status",
    description=(
        "Transition a book's reading status. "
        "Allowed transitions: unread→reading, reading→read, reading→unread."
    ),
)
async def update_book_status(
    book_id: str,
    body: UpdateBookStatusRequest,
    use_case: Annotated[
        UpdateBookStatusUseCase, Depends(provide_update_book_status_use_case)
    ],
) -> BookResponse:
    try:
        dto = UpdateBookStatusInputDTO(book_id=book_id, new_status=body.status)
        result = await use_case.execute(dto)
        return BookResponse(**result.__dict__)
    except BookNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc
    except InvalidBookStatusTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# DELETE /api/v1/books/{book_id} — Delete a book
# ---------------------------------------------------------------------------


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a book",
)
async def delete_book(
    book_id: str,
    use_case: Annotated[DeleteBookUseCase, Depends(provide_delete_book_use_case)],
) -> None:
    try:
        dto = DeleteBookInputDTO(book_id=book_id)
        await use_case.execute(dto)
    except BookNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc
