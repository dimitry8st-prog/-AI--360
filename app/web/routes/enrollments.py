from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.services.course_service import assign_course, list_manageable_courses, list_org_users
from app.web.deps import csrf_from_form, get_db, request_id_of, require_login
from app.web.templating import render

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.get("")
async def assignments_page(
    request: Request,
    user: User = Depends(require_login),
    session: AsyncSession = Depends(get_db),
):
    users = await list_org_users(session, user)
    courses = await list_manageable_courses(session, user)
    return render(request, "assignments.html", title="Назначения", users=users, courses=courses)


@router.post("")
async def assignments_submit(
    request: Request,
    user: User = Depends(require_login),
    session: AsyncSession = Depends(get_db),
    _: str = Depends(csrf_from_form),
    user_id: str = Form(...),
    course_id: str = Form(...),
    deadline: str = Form(""),
):
    parsed_deadline = None
    if deadline.strip():
        parsed_deadline = datetime.fromisoformat(deadline)
        if parsed_deadline.tzinfo is None:
            parsed_deadline = parsed_deadline.replace(tzinfo=UTC)
    await assign_course(
        session,
        actor=user,
        user_id=UUID(user_id),
        course_id=UUID(course_id),
        deadline=parsed_deadline,
        request_id=request_id_of(request),
    )
    return RedirectResponse("/assignments?notice=Курс+назначен", status_code=303)
