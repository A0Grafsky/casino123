from aiogram import F, Router
from aiogram.types import CallbackQuery, Message


from keyboards.inline_keyboard import create_inline_kb
from lexicon.lexicon_ru import LEXICON_RU
from database import database as db


# Реализация роутера
router = Router()


@router.callback_query(F.data == 'coins')
async def handle_coins(callback: CallbackQuery):
    coins = await db.coins_user_from_users(str(callback.from_user.id))
    nickname = await db.nickname_from_users_where_id(str(callback.from_user.id))
    await callback.message.edit_text(text=f'Приветствуем Вас, {nickname[0][0]}\n\n'
                                          f'На Вашем счету:\n\n'
                                          f'<b>Lucky</b>: {coins[0][0]}\n'
                                          f'<b>CashOnline</b>: {coins[0][1]}\n'
                                          f'<b>OtherCoins</b>: {coins[0][2]}\n\n'
                                          f'Что желаете сделать? Напомним, что курс обмена на данный момент таков:\n\n',
                                     reply_markup=create_inline_kb(2, 'trade', 'trade_admin',
                                                                   'history'))
