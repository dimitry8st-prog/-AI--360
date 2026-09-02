"""Exam attempt rules. LLM never confirms qualification by itself."""

from datetime import UTC, datetime, timedelta

from app.core.exceptions import AttemptLockedError, ConflictError, ForbiddenError
from app.db.models.enums import AttemptStatus, QuestionPurpose, QuestionStatus

TERMINAL_ATTEMPT_STATUSES = frozenset(
    {
        AttemptStatus.SUBMITTED.value,
        AttemptStatus.GRADED.value,
        AttemptStatus.NEEDS_REVIEW.value,
        AttemptStatus.COMPLETED.value,
        AttemptStatus.CANCELLED.value,
        AttemptStatus.APPEAL_LOCKED.value,
    }
)

LOCKED_SNAPSHOT_STATUSES = TERMINAL_ATTEMPT_STATUSES | {AttemptStatus.IN_PROGRESS.value}


def can_start_attempt(*, used_attempts: int, attempt_limit: int) -> bool:
    if attempt_limit <= 0:
        return False
    return used_attempts < attempt_limit


def assert_can_start_attempt(*, used_attempts: int, attempt_limit: int) -> None:
    if not can_start_attempt(used_attempts=used_attempts, attempt_limit=attempt_limit):
        raise ConflictError("Исчерпан лимит экзаменационных попыток")


def is_attempt_locked(status: str) -> bool:
    return status in TERMINAL_ATTEMPT_STATUSES


def assert_attempt_mutable(status: str) -> None:
    if is_attempt_locked(status):
        raise AttemptLockedError()


def assert_snapshot_immutable(status: str) -> None:
    """Question/rubric snapshots cannot change after the attempt is created."""
    if status in LOCKED_SNAPSHOT_STATUSES:
        raise AttemptLockedError("Снимок вопросов и рубрики нельзя изменять")


def exam_deadline(started_at: datetime, duration_minutes: int) -> datetime:
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=UTC)
    return started_at + timedelta(minutes=duration_minutes)


def is_time_expired(started_at: datetime, duration_minutes: int, now: datetime | None = None) -> bool:
    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    return current > exam_deadline(started_at, duration_minutes)


def question_eligible_for_exam(*, purpose: str, status: str, generated_by_ai: bool, approved: bool) -> bool:
    if purpose != QuestionPurpose.EXAM.value:
        return False
    if status != QuestionStatus.APPROVED.value:
        return False
    if generated_by_ai and not approved:
        return False
    return True


def score_closed_question(*, expected: str, given: str) -> float:
    return 1.0 if expected.strip().lower() == given.strip().lower() else 0.0


def aggregate_score(*, scores: list[float], max_per_question: float = 1.0) -> tuple[float, float, bool, int]:
    """Returns score, max_score, passed_by_percent, percent."""
    max_score = max_per_question * len(scores)
    total = sum(scores)
    percent = 0 if max_score == 0 else int(round(100 * total / max_score))
    return total, max_score, False, percent


def passed_by_policy(*, percent: int, passing_score: int, requires_human_confirmation: bool, requires_review: bool) -> bool:
    """LLM cannot alone confirm qualification for critical programmes."""
    if requires_human_confirmation or requires_review:
        return False
    return percent >= passing_score


def hide_correct_answers(question_payload: dict) -> dict:
    public = dict(question_payload)
    public.pop("correct_answer", None)
    public.pop("rubric", None)
    return public


def assert_employee_cannot_see_key(roles: set[str], reveal: bool) -> None:
    if "employee" in roles and reveal:
        raise ForbiddenError("Правильный ответ скрыт до завершения попытки")
