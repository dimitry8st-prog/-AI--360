from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import Permission, has_permission
from app.db.models.user import User
from app.services.course_service import (
    add_module,
    create_course,
    get_course,
    list_assigned_courses,
    list_manageable_courses,
    publish_course,
)
from app.web.deps import csrf_from_form, get_db, request_id_of, require_login
from app.web.templating import render

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("")
async def courses_index(
    request: Request,
    user: User = Depends(require_login),
    session: AsyncSession = Depends(get_db),
):
    if has_permission(user.role_names, Permission.COURSE_MANAGE) or has_permission(
        user.role_names, Permission.ENROLLMENT_ASSIGN_TEAM
    ) or has_permission(user.role_names, Permission.ENROLLMENT_ASSIGN_ORG):
        catalog = await list_manageable_courses(session, user)
        assigned = []
    else:
        catalog = []
        assigned = await list_assigned_courses(session, user)
    return render(
        request,
        "courses.html",
        title="Курсы",
        catalog=catalog,
        assigned=assigned,
        can_manage=has_permission(user.role_names, Permission.COURSE_MANAGE),
    )


@router.get("/new")
async def course_new_form(request: Request, user: User = Depends(require_login)):
    if not has_permission(user.role_names, Permission.COURSE_MANAGE):
        return RedirectResponse("/courses?error=Недостаточно+прав", status_code=303)
    return render(request, "course_form.html", title="Новый курс")


@router.post("/new")
async def course_new_submit(
    request: Request,
    user: User = Depends(require_login),
    session: AsyncSession = Depends(get_db),
    _: str = Depends(csrf_from_form),
    title: str = Form(...),
    description: str = Form(""),
    passing_score: int = Form(70),
):
    course = await create_course(
        session,
        actor=user,
        title=title,
        description=description,
        passing_score=passing_score,
        request_id=request_id_of(request),
    )
    return RedirectResponse(f"/courses/{course.id}?notice=Курс+создан", status_code=303)


@router.get("/{course_id}")
async def course_detail(
    course_id: str,
    request: Request,
    user: User = Depends(require_login),
    session: AsyncSession = Depends(get_db),
):
    course = await get_course(session, UUID(course_id))
    return render(
        request,
        "course_detail.html",
        title=course.title,
        course=course,
        can_manage=has_permission(user.role_names, Permission.COURSE_MANAGE),
        can_add_module=has_permission(user.role_names, Permission.MODULE_MANAGE),
    )


@router.post("/{course_id}/publish")
async def course_publish(
    course_id: str,
    request: Request,
    user: User = Depends(require_login),
    session: AsyncSession = Depends(get_db),
    _: str = Depends(csrf_from_form),
):
    await publish_course(
        session, actor=user, course_id=UUID(course_id), request_id=request_id_of(request)
    )
    return RedirectResponse(f"/courses/{course_id}?notice=Курс+опубликован", status_code=303)


@router.get("/{course_id}/modules/new")
async def module_form(
    course_id: str,
    request: Request,
    user: User = Depends(require_login),
):
    if not has_permission(user.role_names, Permission.MODULE_MANAGE):
        return RedirectResponse("/courses?error=Недостаточно+прав", status_code=303)
    return render(request, "module_form.html", title="Новый модуль", course_id=course_id)


@router.post("/{course_id}/modules/new")
async def module_submit(
    course_id: str,
    request: Request,
    user: User = Depends(require_login),
    session: AsyncSession = Depends(get_db),
    _: str = Depends(csrf_from_form),
    title: str = Form(...),
    learning_objectives: str = Form(""),
    estimated_minutes: int = Form(10),
    explain: str = Form(...),
    source_label: str = Form(""),
    recall_prompt: str = Form(...),
    recall_answer: str = Form(""),
    example: str = Form(...),
    check_prompt: str = Form(...),
    check_options: str = Form(...),
    check_answer: str = Form(...),
    alt_body: str = Form(""),
):
    options = [line.strip() for line in check_options.splitlines() if line.strip()]
    await add_module(
        session,
        actor=user,
        course_id=UUID(course_id),
        title=title,
        learning_objectives=learning_objectives,
        estimated_minutes=estimated_minutes,
        explain=explain,
        source_label=source_label,
        recall_prompt=recall_prompt,
        recall_answer=recall_answer,
        example=example,
        check_prompt=check_prompt,
        check_options=options,
        check_answer=check_answer,
        alt_body=alt_body,
        request_id=request_id_of(request),
    )
    return RedirectResponse(f"/courses/{course_id}?notice=Модуль+добавлен", status_code=303)
