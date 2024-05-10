import ast

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.inline_keyboard import create_inline_kb
from database import database as db
from lexicon.lexicon_ru import LEXICON_RU
from config_data.config import Config, load_config

router = Router()
config: Config = load_config()


# Обрабатываем кнопку мен /meny
@router.message(Command(commands='meny'))
async def set_main_meny(message: Message, state: FSMContext):
    await message.delete()
    if message.from_user.id in ast.literal_eval(config.tg_bot.admin_id):
        await state.clear()
        await message.answer(LEXICON_RU['admin_start'],
                             reply_markup=create_inline_kb(2, 'coin_rate', 'Merch_Showcase',
                                                           'clients', 'quizzes', 'message',
                                                           'Сгенерировать QR'))
        await message.bot.delete_message(message.chat.id, message.message_id - 1)
    else:
        await state.clear()
        nickname = await db.nickname_from_users_where_id(str(message.from_user.id))
        await message.answer(LEXICON_RU['start'] + f'\n\n❗<b>Ваш ник - {nickname[0][0]}</b>\n\n'
                             + f'❗<b>Ваш id - {message.from_user.id}</b>',
                             reply_markup=create_inline_kb(2, 'coins', 'merch',
                                                           'referral', 'Статистика рефералов', 'Получить бонусы'))
        await message.bot.delete_message(message.chat.id, message.message_id - 1)


# Обработчик кнопки вернуться назад
@router.callback_query(F.data == 'back')
async def back_button(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id in ast.literal_eval(config.tg_bot.admin_id):
        await state.clear()
        await callback.message.answer(LEXICON_RU['admin_start'],
                             reply_markup=create_inline_kb(2, 'coin_rate', 'Merch_Showcase',
                                                           'clients', 'quizzes', 'message',
                                                           'Сгенерировать QR'))
    else:
        await state.clear()
        nickname = await db.nickname_from_users_where_id(str(callback.from_user.id))
        await callback.message.answer(LEXICON_RU['start'] + f'\n\n❗<b>Ваш ник - {nickname[0][0]}</b>\n\n'
                             + f'❗<b>Ваш id - {callback.from_user.id}</b>',
                             reply_markup=create_inline_kb(2, 'coins', 'merch',
                                                           'referral', 'Статистика рефералов', 'Получить бонусы'))


# Обработчик кнопки назад, которая используется в местах где нужно оправлять новое сообщение
@router.callback_query(F.data == 'back_delete')
async def back_button_delete(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id in ast.literal_eval(config.tg_bot.admin_id):
        await state.clear()
        await callback.message.delete()
        await callback.message.answer(LEXICON_RU['admin_start'],
                             reply_markup=create_inline_kb(2, 'coin_rate', 'Merch_Showcase',
                                                           'clients', 'quizzes', 'message',
                                                           'Сгенерировать QR'))
    else:
        await state.clear()
        await callback.message.delete()
        nickname = await db.nickname_from_users_where_id(str(callback.from_user.id))
        await callback.message.answer(LEXICON_RU['start'] + f'\n\n❗<b>Ваш ник - {nickname[0][0]}</b>\n\n'
                             + f'❗<b>Ваш id - {callback.from_user.id}</b>',
                             reply_markup=create_inline_kb(2, 'coins', 'merch',
                                                           'referral', 'Статистика рефералов', 'Получить бонусы'))

# Лови все мир
@router.message(F.text)
async def musor(message: Message):
    await message.answer(f'Команда <b>{message.text}</b> не поддерживается')











