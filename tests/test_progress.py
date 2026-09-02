from app.services.progress_service import calc_module_progress, enrollment_is_overdue


def test_progress_zero_when_no_modules():
    assert calc_module_progress(completed_modules=0, total_modules=0) == 0


def test_progress_clamped():
    assert calc_module_progress(completed_modules=3, total_modules=8) == 38
    assert calc_module_progress(completed_modules=8, total_modules=8) == 100
    assert calc_module_progress(completed_modules=99, total_modules=8) == 100
    assert calc_module_progress(completed_modules=-1, total_modules=8) == 0


def test_overdue_skips_completed():
    assert enrollment_is_overdue(status="in_progress", deadline_passed=True) is True
    assert enrollment_is_overdue(status="completed", deadline_passed=True) is False
    assert enrollment_is_overdue(status="assigned", deadline_passed=False) is False
