from aiogram.fsm.state import State, StatesGroup


class LinkAccount(StatesGroup):
    email = State()


class Learn(StatesGroup):
    recall = State()
    check = State()
