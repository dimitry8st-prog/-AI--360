"""Progress is a server-side calculation, not an LLM opinion."""


def calc_module_progress(*, completed_modules: int, total_modules: int) -> int:
    if total_modules <= 0:
        return 0
    completed = max(0, min(completed_modules, total_modules))
    return int(round(100 * completed / total_modules))


def enrollment_is_overdue(*, status: str, deadline_passed: bool) -> bool:
    if status in {"completed", "cancelled"}:
        return False
    return deadline_passed
