"""Uniform public errors and safe request correlation for FastAPI."""

import logging
import re
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)
_REQUEST_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z", re.ASCII)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or str(uuid4())


def _error(request: Request, status: int, code: str, message: str) -> JSONResponse:
    request_id = _request_id(request)
    # A route *template* is application code, not a URL with IDs/query values.
    route = request.scope.get("route")
    route_template = getattr(route, "path", "<unmatched>")
    # Never log the exception, actual URL, headers, validation details or body.
    logger.log(
        logging.ERROR if status >= 500 else logging.WARNING,
        "Request failed code=%s status=%s request_id=%s route=%s",
        code,
        status,
        request_id,
        route_template,
    )
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "request_id": request_id}},
        headers={"X-Request-ID": request_id},
    )


def register_handlers(app: FastAPI) -> None:
    """Install middleware/handlers before the app starts; safe to call twice."""
    # COM-02 owns these exception types. Import here so schemas and this module
    # remain independently importable while the base branch is being assembled.
    from .contracts import DuplicateEvent, EventNotFound, StorageUnavailable

    if getattr(app.state, "_event_error_handlers_registered", False):
        return
    app.state._event_error_handlers_registered = True

    @app.middleware("http")
    async def correlate_request(request: Request, call_next):
        supplied = request.headers.getlist("x-request-id")
        request.state.request_id = (
            supplied[0]
            if len(supplied) == 1 and _REQUEST_ID.fullmatch(supplied[0])
            else str(uuid4())
        )
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_input(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _error(request, 422, "INVALID_INPUT", "Invalid request input.")

    @app.exception_handler(DuplicateEvent)
    async def duplicate(request: Request, exc: DuplicateEvent) -> JSONResponse:
        return _error(request, 409, "DUPLICATE", "Event already exists.")

    @app.exception_handler(EventNotFound)
    async def missing(request: Request, exc: EventNotFound) -> JSONResponse:
        return _error(request, 404, "NOT_FOUND", "Resource not found.")

    @app.exception_handler(StorageUnavailable)
    async def dependency(request: Request, exc: StorageUnavailable) -> JSONResponse:
        return _error(request, 503, "DEPENDENCY_UNAVAILABLE", "Dependency unavailable.")

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        public = {
            401: ("UNAUTHENTICATED", "Authentication required."),
            403: ("FORBIDDEN", "Access denied."),
            404: ("NOT_FOUND", "Resource not found."),
        }
        if exc.status_code in public:
            code, message = public[exc.status_code]
            return _error(request, exc.status_code, code, message)
        if 400 <= exc.status_code < 500:
            return _error(request, exc.status_code, "INVALID_INPUT", "Invalid request.")
        return _error(request, 500, "INTERNAL_ERROR", "Internal server error.")

    @app.exception_handler(Exception)
    async def unexpected(request: Request, exc: Exception) -> JSONResponse:
        return _error(request, 500, "INTERNAL_ERROR", "Internal server error.")
