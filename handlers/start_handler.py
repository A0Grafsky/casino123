import ast

import aiosqlite
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
class UserNicknameState(StatesGroup):
    waiting_nick = State()


# Этот хэндлер будет срабатывать на команду "/start" -
# Отправлять ему текст и клавиатуру
@router.message(CommandStart())
async def process_command_start(message: Message, state: FSMContext):
    await message.delete()
    await state.clear()
    print(ast.literal_eval(config.tg_bot.admin_id))
    if len(message.text.split(' ')) == 1:
        if (message.from_user.id not in [i[0] for i in (await db.user_id_from_users())]
                and not message.from_user.id in ast.literal_eval(config.tg_bot.admin_id)):
            await message.answer(LEXICON_RU['load_nickname_for_user'])
            await state.set_state(UserNicknameState.waiting_nick)
        else:
            if message.from_user.id in ast.literal_eval(config.tg_bot.admin_id):
                await state.clear()
                await db.add_admin_to_admin_table(str(message.from_user.id), message.from_user.username,
                                                  10000, 10000, 10000)
                # Тут будет копка + текст (админ)
                await message.answer(LEXICON_RU['admin_start'],
                                     reply_markup=create_inline_kb(2, 'coin_rate', 'Merch_Showcase',
                                                                   'clients', 'quizzes', 'message', 'Сгенерировать QR', 'Посмотреть рефералов'))
            else:
                # Тут будет кнопка + текст (юзер)
                await state.clear()
                nickname = await db.nickname_from_users_where_id(str(message.from_user.id))
                await message.answer(LEXICON_RU['start'] + f'\n\n❗<b>Ваш ник - {nickname[0][0]}</b>\n\n'
                                     + f'❗<b>Ваш id - {message.from_user.id}</b>',
                                     reply_markup=create_inline_kb(2, 'coins', 'merch',
                                                                   'referral', 'Статистика рефералов', 'Получить бонусы'))
    elif len(message.text.split(' ')) == 2:
        if (message.from_user.id not in [i[0] for i in (await db.user_id_from_users())]
                and not message.from_user.id in ast.literal_eval(config.tg_bot.admin_id)):
            await message.answer(LEXICON_RU['load_nickname_for_user'])
            await state.update_data(referral_id = message.text.split(' ')[1])
            await state.set_state(UserNicknameState.waiting_nick)
        else:
            nickname = await db.nickname_from_users_where_id(str(message.from_user.id))
            await message.answer(LEXICON_RU['start'] + f'\n\n❗<b>Ваш ник - {nickname[0][0]}</b>\n\n'
                                 + f'❗<b>Ваш id - {message.from_user.id}</b>',
                                 reply_markup=create_inline_kb(2, 'coins', 'merch',
                                                               'referral', 'Статистика рефералов', 'Получить бонусы'))
            await state.clear()


# Регистрация ника в БД
@router.message(StateFilter(UserNicknameState.waiting_nick), F.text)
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
    print(data)
    if nickname not in [i[0] for i in (await db.nickname_from_users())]:
        await db.add_user_to_users_table(str(message.from_user.id), message.from_user.username,
                                         nickname, 0, 0, 0, 0, current_time)
        if 'referral_id' in data.keys():
            if data['referral_id'] != str(message.from_user.id):
                async with aiosqlite.connect('userdata.db') as conn:
                    await conn.execute('UPDATE users SET referral = ? WHERE user_id = ?', (data['referral_id'], message.from_user.id))
                    await conn.commit()
                    get_lucky_coins = await conn.execute('SELECT Lucky FROM users WHERE user_id = ?', (data['referral_id'], ))
                    get_lucky_coins = await get_lucky_coins.fetchall()
                    await conn.execute('UPDATE users SET Lucky = ? WHERE user_id = ?', (get_lucky_coins[0][0] + 3, data['referral_id']))
                    await conn.commit()
                await message.answer(f'Вы зашли по реферральной ссылке человека, с id {data["referral_id"]}')
            else:
                await message.answer('Вы зашли по собственной реферальной ссылке.')
        await message.answer(f'{nickname} - успешно зарегистрирован\n\n')
        await state.clear()
        await message.answer(LEXICON_RU['start'] + f'\n\n❗<b>Ваш ник - {nickname[0]}</b>\n\n'
                             + f'❗<b>Ваш id - {message.from_user.id}</b>',
                             reply_markup=create_inline_kb(2, 'coins', 'merch',
                                                           'referral', 'Статистика рефералов', 'Получить бонусы'))
    else:
        await message.answer(f'{nickname} - уже занят, попробуйте другой)')


