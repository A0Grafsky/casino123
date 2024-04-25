from aiogram import F, Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from config_data.config import Config, load_config
from keyboards.inline_keyboard import create_inline_kb
from lexicon.lexicon_ru import LEXICON_RU
from database import database as db

# Реализация роутера
router = Router()
config: Config = load_config()


# Реализация класса состояния
class user_nickname_state(StatesGroup):
    waiting_nick = State()


# Этот хэндлер будет срабатывать на команду "/start" -
# Отправлять ему текст и клавиатуру
@router.message(CommandStart())
async def process_command_start(message: Message, state: FSMContext):
    if (message.from_user.id not in [i[0] for i in (await db.user_id_from_users())]
            and not message.from_user.id == int(config.tg_bot.admin_id)):
        await message.answer(LEXICON_RU['load_nickname_for_user'])
        await state.set_state(user_nickname_state.waiting_nick)

    else:
        if message.from_user.id == int(config.tg_bot.admin_id):
            await db.add_admin_to_admin_table(str(message.from_user.id), message.from_user.username,
                                              10000, 10000, 10000)
            # Тут будет копка + текст (админ)
            await message.answer(LEXICON_RU['admin_start'])
        else:
            # Тут будет кнопка + текст (юзер)
            await message.answer(LEXICON_RU['start'], reply_markup=create_inline_kb(2, 'coins', 'merch',
                                                                                    'referral'))


# Регистрация ника в БД
@router.message(StateFilter(user_nickname_state.waiting_nick), F.text)
async def append_user_to_user_tabl(message: Message, state: FSMContext):
    current_time = datetime.now().isoformat()
    if message.text.__contains__('/'):
        await message.answer('Нельзя использовать "/"')
    elif message.text.__contains__('admin' or 'админ'):
        await message.answer(f'Ник {message.text} - запрещен')
    else:
        await state.update_data(nickname=message.text)
    data = await state.get_data()
    nickname = data['nickname']
    if nickname not in [i[0] for i in (await db.nickname_from_users())]:
        await db.add_user_to_users_table(str(message.from_user.id), message.from_user.username,
                                         nickname, 0, 0, 0, current_time)
        await message.answer(f'{nickname} - успешно зарегистрирован\n\n')
        await state.clear()
        # тут логика для обычного пользователя
        await message.answer(LEXICON_RU['start'], reply_markup=create_inline_kb(2, 'coins', 'merch',
                                                                                'referral'))
    else:
        await message.answer(f'{nickname} - уже занят, попробуйте другой)')
