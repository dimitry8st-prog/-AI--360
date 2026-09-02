class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, *, code: str = "app_error", status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class NotFoundError(AppError):
    def __init__(self, message: str = "Объект не найден"):
        super().__init__(message, code="not_found", status_code=404)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Недостаточно прав"):
        super().__init__(message, code="forbidden", status_code=403)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Требуется авторизация"):
        super().__init__(message, code="unauthorized", status_code=401)


class ConflictError(AppError):
    def __init__(self, message: str = "Конфликт состояния"):
        super().__init__(message, code="conflict", status_code=409)


class AttemptLockedError(AppError):
    def __init__(self, message: str = "Попытка зафиксирована и не может быть изменена"):
        super().__init__(message, code="attempt_locked", status_code=409)


class AIUnavailableError(AppError):
    def __init__(self, message: str = "AI-провайдер недоступен, используется ручной режим"):
        super().__init__(message, code="ai_unavailable", status_code=503)


class ValidationAppError(AppError):
    def __init__(self, message: str = "Ошибка валидации"):
        super().__init__(message, code="validation_error", status_code=422)


class RateLimitError(AppError):
    def __init__(self, message: str = "Слишком много запросов, подождите немного"):
        super().__init__(message, code="rate_limited", status_code=429)
