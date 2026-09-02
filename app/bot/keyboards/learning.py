from uuid import UUID

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.db.models.course import Course, Enrollment, LearningBlock


def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Мои курсы", callback_data="menu:courses")],
            [InlineKeyboardButton(text="Справка", callback_data="menu:help")],
        ]
    )


def courses_keyboard(rows: list[tuple[Course, Enrollment]]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=course.title[:60], callback_data=f"open:{course.id}")]
        for course, _enrollment in rows
    ]
    if not buttons:
        buttons = [[InlineKeyboardButton(text="Обновить", callback_data="menu:courses")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def next_keyboard(session_id: UUID) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Далее", callback_data=f"next:{session_id}")]]
    )


def check_keyboard(session_id: UUID, block: LearningBlock) -> InlineKeyboardMarkup:
    options = block.options_json or []
    rows = [
        [InlineKeyboardButton(text=option[:60], callback_data=f"chk:{session_id}:{index}")]
        for index, option in enumerate(options)
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows or [[InlineKeyboardButton(text="Далее", callback_data=f"next:{session_id}")]])
