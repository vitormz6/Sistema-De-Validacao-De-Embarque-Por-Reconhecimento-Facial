from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class DomainError(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(DomainError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)


class ConflictError(DomainError):
    def __init__(self, message: str = "Resource conflict") -> None:
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT)


class ValidationFailedError(DomainError):
    def __init__(self, message: str = "Validation failed") -> None:
        # Literal status code: Starlette has renamed the 422 constant across
        # versions (HTTP_422_UNPROCESSABLE_ENTITY -> _CONTENT); the numeric
        # value itself is stable, so we avoid depending on either name.
        super().__init__(message=message, status_code=422)


class UnauthorizedError(DomainError):
    def __init__(self, message: str = "Invalid authentication credentials") -> None:
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(DomainError):
    def __init__(self, message: str = "You do not have permission to perform this action") -> None:
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN)


class UpstreamServiceError(DomainError):
    def __init__(self, message: str = "Upstream service error") -> None:
        super().__init__(message=message, status_code=status.HTTP_502_BAD_GATEWAY)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": exc.__class__.__name__,
                    "message": exc.message,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "type": "InternalServerError",
                    "message": "Unexpected internal server error.",
                }
            },
        )
