from typing import Optional, Any, Dict
from pydantic import BaseModel, Field
from fastapi import Request
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger()


class ErrorDetail(BaseModel):
    """Standardized error detail structure."""
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field name for validation errors")


class ErrorResponse(BaseModel):
    """Standardized API error response format."""
    error: ErrorDetail
    correlation_id: Optional[str] = Field(None, description="Request correlation ID for tracing")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")


# Error codes
class ErrorCodes:
    # Authentication errors
    UNAUTHENTICATED = "UNAUTHENTICATED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"

    # Authorization errors
    FORBIDDEN = "FORBIDDEN"
    INSUFFICIENT_ROLE = "INSUFFICIENT_ROLE"
    CROSS_TENANT_ACCESS = "CROSS_TENANT_ACCESS"

    # Resource errors
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    CONFLICT = "CONFLICT"

    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"

    # Processing errors
    PROCESSING_FAILED = "PROCESSING_FAILED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    EMBEDDING_FAILED = "EMBEDDING_FAILED"

    # Approval errors
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVAL_EXPIRED = "APPROVAL_EXPIRED"
    APPROVAL_DENIED = "APPROVAL_DENIED"
    APPROVAL_NOT_FOUND = "APPROVAL_NOT_FOUND"

    # Internal errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"


class AppException(Exception):
    """Base application exception with structured error details."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.field = field
        self.details = details or {}
        super().__init__(message)


class AuthenticationError(AppException):
    def __init__(self, message: str = "Authentication required", code: str = ErrorCodes.UNAUTHENTICATED):
        super().__init__(code=code, message=message, status_code=401)


class AuthorizationError(AppException):
    def __init__(self, message: str = "Access denied", code: str = ErrorCodes.FORBIDDEN):
        super().__init__(code=code, message=message, status_code=403)


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found", resource_type: str = "resource"):
        super().__init__(
            code=ErrorCodes.NOT_FOUND,
            message=message,
            status_code=404,
            details={"resource_type": resource_type}
        )


class ConflictError(AppException):
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(code=ErrorCodes.CONFLICT, message=message, status_code=409)


class ValidationError(AppException):
    def __init__(self, message: str = "Validation failed", field: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(
            code=ErrorCodes.VALIDATION_ERROR,
            message=message,
            status_code=422,
            field=field,
            details=details
        )


class ProcessingError(AppException):
    def __init__(self, message: str = "Processing failed", code: str = ErrorCodes.PROCESSING_FAILED):
        super().__init__(code=code, message=message, status_code=500)


class ApprovalError(AppException):
    def __init__(self, message: str = "Approval required", code: str = ErrorCodes.APPROVAL_REQUIRED):
        super().__init__(code=code, message=message, status_code=409)


def create_error_response(
    request: Request,
    code: str,
    message: str,
    status_code: int = 400,
    field: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Create a standardized error response with correlation ID."""
    correlation_id = getattr(request.state, "correlation_id", None)

    error_detail = ErrorDetail(code=code, message=message, field=field)
    error_response = ErrorResponse(
        error=error_detail,
        correlation_id=correlation_id,
        details=details,
    )

    logger.warning(
        "api_error",
        correlation_id=correlation_id,
        code=code,
        message=message,
        status_code=status_code,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(exclude_none=True),
    )


# Exception handlers for FastAPI
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return create_error_response(
        request,
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        field=exc.field,
        details=exc.details,
    )


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle Pydantic validation errors."""
    correlation_id = getattr(request.state, "correlation_id", None)

    # Try to extract field info from validation error
    field = None
    message = "Validation failed"
    details = {}

    if hasattr(exc, "errors"):
        errors = exc.errors()
        if errors:
            first_error = errors[0]
            field = ".".join(str(loc) for loc in first_error.get("loc", []))
            message = first_error.get("msg", message)
            details = {"validation_errors": errors}

    error_detail = ErrorDetail(code=ErrorCodes.VALIDATION_ERROR, message=message, field=field)
    error_response = ErrorResponse(
        error=error_detail,
        correlation_id=correlation_id,
        details=details,
    )

    logger.warning(
        "validation_error",
        correlation_id=correlation_id,
        errors=errors if hasattr(exc, "errors") else str(exc),
        path=request.url.path,
    )

    return JSONResponse(
        status_code=422,
        content=error_response.model_dump(exclude_none=True),
    )