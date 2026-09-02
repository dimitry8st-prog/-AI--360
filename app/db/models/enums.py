from enum import StrEnum


class OrgStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class UserStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    INVITED = "invited"


class CourseStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class DocumentStatus(StrEnum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    ARCHIVED = "archived"


class SourceType(StrEnum):
    UPLOAD = "upload"
    URL = "url"
    MANUAL = "manual"


class AccessScope(StrEnum):
    ORGANIZATION = "organization"
    DEPARTMENT = "department"
    COURSE = "course"


class EnrollmentStatus(StrEnum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class BlockType(StrEnum):
    EXPLAIN = "explain"
    SOURCE = "source"
    RECALL = "recall"
    EXAMPLE = "example"
    CHECK = "check"


class SessionState(StrEnum):
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"


class QuestionType(StrEnum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    OPEN = "open"
    CASE = "case"


class QuestionPurpose(StrEnum):
    TRAINING = "training"
    EXAM = "exam"


class QuestionStatus(StrEnum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


class ExamStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AttemptStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    GRADED = "graded"
    NEEDS_REVIEW = "needs_review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    APPEAL_LOCKED = "appeal_locked"


class GraderType(StrEnum):
    DETERMINISTIC = "deterministic"
    LLM_EXAMINER = "llm_examiner"
    HUMAN = "human"
    STUB = "stub"


class AppealStatus(StrEnum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    UPHELD = "upheld"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class NextAction(StrEnum):
    CONTINUE = "continue"
    REPEAT = "repeat"
    PRACTICE = "practice"
    ESCALATE = "escalate"
