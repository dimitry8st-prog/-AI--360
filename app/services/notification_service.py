from datetime import UTC, datetime

from app.core.logging import get_logger
from app.db.models.course import Enrollment
from app.db.models.enums import EnrollmentStatus

logger = get_logger("notification")


def refresh_enrollment_status(enrollment: Enrollment, *, now: datetime | None = None) -> Enrollment:
    current = now or datetime.now(UTC)
    if enrollment.status in {EnrollmentStatus.COMPLETED.value, EnrollmentStatus.CANCELLED.value}:
        return enrollment
    if enrollment.deadline is not None:
        deadline = enrollment.deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=UTC)
        if current > deadline and enrollment.status != EnrollmentStatus.OVERDUE.value:
            enrollment.status = EnrollmentStatus.OVERDUE.value
            logger.info(
                "enrollment_marked_overdue",
                enrollment_id=str(enrollment.id),
                user_id=str(enrollment.user_id),
                course_id=str(enrollment.course_id),
            )
    return enrollment
