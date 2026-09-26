class AppError(Exception):
    """Expected application failure with a safe client message."""

    code = "UNKNOWN_ERROR"
    status_code = 500


class NotFoundError(AppError):
    code = "NOT_FOUND"
    status_code = 404


class ValidationFailed(AppError):
    code = "VALIDATION_ERROR"
    status_code = 422


class AuthenticationFailed(AppError):
    code = "AUTHENTICATION_ERROR"
    status_code = 401


class AuthorizationFailed(AppError):
    code = "FORBIDDEN"
    status_code = 403


class ConnectionFailed(AppError):
    code = "CONNECTION_ERROR"
    status_code = 502


class TimeoutFailed(AppError):
    code = "TIMEOUT"
    status_code = 504


class CommandFailed(AppError):
    code = "COMMAND_ERROR"
    status_code = 400


class ParserFailed(AppError):
    code = "PARSER_ERROR"
    status_code = 422


class CollectorFailed(AppError):
    code = "COLLECTOR_ERROR"
    status_code = 500


class StorageFailed(AppError):
    code = "STORAGE_ERROR"
    status_code = 500


class ConnectionCheckError(ConnectionFailed):
    """Dependency probe failed."""
