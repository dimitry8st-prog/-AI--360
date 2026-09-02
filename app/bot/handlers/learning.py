from html import escape
from uuid import UUID

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.learning import (
    check_keyboard,
    courses_keyboard,
    next_keyboard,
    start_keyboard,
)
from app.bot.states.learning import Learn, LinkAccount
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.db.models.enums import BlockType
from app.db.models.user import User
from app.services.auth_service import bind_telegram
from app.services.course_service import get_course, list_assigned_courses
from app.services.learning_service import (
    BlockView,
    advance_content_block,
    current_view,
    latest_session,
    own_progress_payload,
    start_or_resume,
    submit_check,
    submit_recall,
)
from app.services.learning_service import (
    get_session as get_learning_session,
)

router = Router(name="learning")
logger = get_logger("bot.learning")

HELP_TEXT = (
    "ДИС — цифровой лис, AI-наставник 360.\n\n"
    "Я помогаю учиться по утверждённым материалам. Кадровые решения я не принимаю "
    "и квалификацию не подтверждаю.\n\n"
    "/start — начало и привязка\n"
    "/courses — назначенные курсы\n"
    "/continue — продолжить обучение\n"
    "/progress — личный прогресс\n"
    "/help — справка\n"
    "/practice и /exam появятся позже."
)


def _need_user(message_or_cb) -> str:
    return "Сначала привяжите профиль: отправьте рабочий email или /start."


def format_block(view: BlockView) -> str:
    block = view.block
    parts = [
        f"<b>{escape(view.module_title)}</b>",
        f"Прогресс курса: {view.progress_percent}%",
        "",
        f"<b>{escape(block.title or block.block_type)}</b>",
    ]
    if block.body:
        parts.append(escape(block.body))
    if block.source_label:
        parts.append(f"Источник: {escape(block.source_label)}")
    if block.prompt:
        parts.append(escape(block.prompt))
    if view.feedback:
        parts.extend(["", escape(view.feedback)])
    parts.append("\nЯ не выставляю итоговую квалификацию — это шаг обучения.")
    return "\n".join(parts)


async def _send_view(target: Message, view: BlockView | None, state: FSMContext) -> None:
    if view is None:
        await state.clear()
        await target.answer("Курс по учебным блокам завершён. Квалификацию это не подтверждает.")
        return
    await state.update_data(session_id=str(view.session_id))
    if view.block.block_type == BlockType.RECALL.value:
        await state.set_state(Learn.recall)
        await target.answer(format_block(view), reply_markup=None)
        return
    if view.block.block_type == BlockType.CHECK.value:
        await state.set_state(Learn.check)
        await target.answer(format_block(view), reply_markup=check_keyboard(view.session_id, view.block))
        return
    await state.set_state(None)
    await target.answer(format_block(view), reply_markup=next_keyboard(view.session_id))


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db_user: User | None) -> None:
    await state.clear()
    if db_user:
        logger.info("bot_start_known")
        await message.answer(
            f"Привет, {escape(db_user.full_name)}. Я ДИС.\n"
            "Откройте /courses, чтобы начать назначенную программу.",
            reply_markup=start_keyboard(),
        )
        return
    await state.set_state(LinkAccount.email)
    await message.answer(
        "Привет. Я ДИС, цифровой лис.\n\n"
        "Чтобы открыть ваши курсы, отправьте рабочий email, который занёс администратор. "
        "Я не принимаю кадровые решения."
    )


@router.message(LinkAccount.email)
async def link_email(message: Message, state: FSMContext, session: AsyncSession) -> None:
    email = (message.text or "").strip()
    if "@" not in email:
        await message.answer("Нужен рабочий email, например employee@demo.local")
        return
    try:
        user = await bind_telegram(session, email=email, telegram_id=message.from_user.id)
    except AppError as exc:
        await message.answer(exc.message)
        return
    await state.clear()
    await message.answer(
        f"Профиль связан: {escape(user.full_name)}. Откройте /courses.",
        reply_markup=start_keyboard(),
    )


@router.message(Command("help"))
@router.callback_query(F.data == "menu:help")
async def cmd_help(event: Message | CallbackQuery) -> None:
    if isinstance(event, CallbackQuery):
        await event.answer()
        if event.message:
            await event.message.answer(HELP_TEXT)
        return
    await event.answer(HELP_TEXT)


@router.message(Command("courses"))
@router.callback_query(F.data == "menu:courses")
async def cmd_courses(
    event: Message | CallbackQuery,
    session: AsyncSession,
    db_user: User | None,
) -> None:
    message = event if isinstance(event, Message) else event.message
    if isinstance(event, CallbackQuery):
        await event.answer()
    if db_user is None or message is None:
        if message:
            await message.answer(_need_user(event))
        return
    rows = await list_assigned_courses(session, db_user)
    if not rows:
        await message.answer("Вам пока не назначены программы. Руководитель сделает это в панели.")
        return
    await message.answer("Назначенные программы:", reply_markup=courses_keyboard(rows))


@router.callback_query(F.data.startswith("open:"))
async def open_course(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User | None,
    state: FSMContext,
) -> None:
    await callback.answer()
    if db_user is None or callback.message is None:
        return
    course_id = UUID(callback.data.split(":", 1)[1])
    course = await get_course(session, course_id)
    modules = "\n".join(f"{m.position}. {m.title} ({m.estimated_minutes} мин)" for m in course.modules)
    await callback.message.answer(
        f"<b>{escape(course.title)}</b>\n{escape(course.description)}\n\n"
        f"Как завершить: пройти все модули. Порог знакомства {course.passing_score}%. "
        f"Это не кадровое решение и не аттестация.\n\nСтруктура:\n{escape(modules)}"
    )
    learning = await start_or_resume(session, user=db_user, course_id=course_id)
    view = await current_view(session, learning, db_user)
    await _send_view(callback.message, view, state)


@router.message(Command("continue"))
async def cmd_continue(
    message: Message,
    session: AsyncSession,
    db_user: User | None,
    state: FSMContext,
) -> None:
    if db_user is None:
        await message.answer(_need_user(message))
        return
    learning = await latest_session(session, db_user)
    if learning is None:
        await message.answer("Нет активной сессии. Откройте /courses.")
        return
    view = await current_view(session, learning, db_user)
    await _send_view(message, view, state)


@router.callback_query(F.data.startswith("next:"))
async def next_block(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User | None,
    state: FSMContext,
) -> None:
    await callback.answer()
    if db_user is None or callback.message is None:
        return
    session_id = UUID(callback.data.split(":", 1)[1])
    view = await advance_content_block(session, user=db_user, session_id=session_id)
    await _send_view(callback.message, view, state)


@router.message(Learn.recall)
async def recall_answer(
    message: Message,
    session: AsyncSession,
    db_user: User | None,
    state: FSMContext,
) -> None:
    if db_user is None:
        await message.answer(_need_user(message))
        return
    data = await state.get_data()
    view = await submit_recall(
        session, user=db_user, session_id=UUID(data["session_id"]), answer=message.text or ""
    )
    await _send_view(message, view, state)


@router.callback_query(F.data.startswith("chk:"), Learn.check)
async def check_answer(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User | None,
    state: FSMContext,
) -> None:
    await callback.answer()
    if db_user is None or callback.message is None or not callback.data:
        return
    _prefix, raw_session_id, index_s = callback.data.split(":", 2)
    current = await get_learning_session(session, UUID(raw_session_id), db_user)
    view = await current_view(session, current, db_user)
    options = (view.block.options_json if view else None) or []
    try:
        answer = options[int(index_s)]
    except (ValueError, IndexError):
        await callback.message.answer("Некорректный вариант.")
        return
    result = await submit_check(session, user=db_user, session_id=UUID(raw_session_id), answer=answer)
    await _send_view(callback.message, result, state)


@router.message(Command("progress"))
async def cmd_progress(message: Message, session: AsyncSession, db_user: User | None) -> None:
    if db_user is None:
        await message.answer(_need_user(message))
        return
    rows = await own_progress_payload(session, db_user)
    if not rows:
        await message.answer("Назначенных курсов нет.")
        return
    lines = [
        f"{row['title']}: {row['percent']}% ({row['completed_modules']}/{row['total_modules']}), статус {row['status']}"
        for row in rows
    ]
    await message.answer("Личный прогресс:\n" + "\n".join(lines))


@router.message(Command("practice", "exam", "appeal"))
async def cmd_later(message: Message) -> None:
    await message.answer("Эта команда появится на следующих этапах (практика, экзамен, апелляция).")
