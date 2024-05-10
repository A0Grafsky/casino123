import json
import os
import random

from aiogram import F, Router
from aiogram.enums import ChatMemberStatus
from aiogram.types import CallbackQuery, Message, FSInputFile, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from datetime import datetime
import aiosqlite
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.inline_keyboard import create_inline_kb
from config_data.config import Config, load_config
from lexicon.lexicon_ru import LEXICON_RU
from database import database as db
from workers.qr_code import QRCode

# Реализация роутера
router = Router()
config: Config = load_config()


# Реализация класса состояния
class TradeUserCoins(StatesGroup):
    choose_trade_type = State()
    lucky_to_cash = State()
    cash_to_chips = State()
    accept_lucky_cash_trade = State()
    accept_cash_chips_trade = State()


# Реализация кнопки 'монета', обмен, трейдинг с админом
@router.callback_query(F.data == 'coins')
async def handle_coins(callback: CallbackQuery):
    coins = await db.coins_user_from_users(str(callback.from_user.id))
    nickname = await db.nickname_from_users_where_id(str(callback.from_user.id))
    await callback.message.edit_text(text=f'Приветствуем Вас, {nickname[0][0]}\n\n'
                                          f'На Вашем счету:\n\n'
                                          f'<b>Lucky</b>: {coins[0][0]}\n'
                                          f'<b>CashOnline</b>: {coins[0][1]}\n'
                                          f'<b>OtherCoins</b>: {coins[0][2]}\n'
                                          f'<b>Chips</b>: {coins[0][3]}\n\n'
                                          f'Что желаете сделать?',
                                     reply_markup=create_inline_kb(2, 'trade', 'trade_admin',
                                                                   'history', last_btn='back'))

@router.callback_query(F.data == 'history')
async def get_history_transactions(callback: CallbackQuery):
    await callback.message.answer('Вы можете посмотреть историю своих транзакций, перейдя по этой ссылке - \n'
                                  f'https://{config.tg_bot.ipv4}:8000/transactions?user_id=1252901622 ')


# Обработка кнопки обмен, тут происходит логика обмена
@router.callback_query(F.data == 'trade')
async def trade_user_coins(callback: CallbackQuery, state: FSMContext):
    coins = await db.coins_user_from_users(str(callback.from_user.id))
    rate_coin = await db.if_rate_coins_for_table()
    await callback.message.edit_text(text=f'🪙На Вашем счету🪙\n\n'
                                          f'<b>Lucky</b>: {coins[0][0]}\n'
                                          f'<b>CashOnline</b>: {coins[0][1]}\n'
                                          f'<b>OtherCoins</b>: {coins[0][2]}\n\n'
                                          f'❗ВАЖНО❗\n\n'
                                          f'На данный момент можно обменять Lucky на CashOnline, а также CashOnline на фишки. Если '
                                          f'Вы хотите совершить обмен, то <u><b>выберите что хотите обменять из двух вариантов и напишите количество монет, '
                                          f'которые хотите обменять, учитывая курс</b></u>, '
                                          f'если Вы не хотите этого, то нажмите на кнопку "Отменить"\n\n'
                                          f'<u><b>Курс на данный момент:</b></u>\n\n'
                                          f'Одна монета {rate_coin[0][1]} стоит {rate_coin[0][2]}\n'
                                          f'Одна фишка стоит {str(rate_coin[1][2])} {rate_coin[1][0]}\n\n',
                                     reply_markup=create_inline_kb(1, *['Lucky на CashOnline', 'CashOnline на фишки'], last_btn='back_delete'))
    await state.set_state(TradeUserCoins.choose_trade_type)

@router.callback_query(F.data.in_(['Lucky на CashOnline', 'CashOnline на фишки']), TradeUserCoins.choose_trade_type)
async def trade_lucky_to_online(callback: CallbackQuery, state:FSMContext):
    if callback.data == 'Lucky на CashOnline':
        await callback.message.answer('Введите количество монет Lucky, которое выхотите обменять на CashOnline')
        await state.set_state(TradeUserCoins.lucky_to_cash)
    if callback.data == 'CashOnline на фишки':
        await callback.message.answer('Введите количество монет CashOnline, которое выхотите обменять на фишки')
        await state.set_state(TradeUserCoins.cash_to_chips)

@router.message(F.text, StateFilter(*[TradeUserCoins.lucky_to_cash, TradeUserCoins.cash_to_chips]))
async def input_trade(message: Message, state: FSMContext):
    if await state.get_state() == TradeUserCoins.lucky_to_cash:
        current_time = datetime.now().isoformat()
        rate_coin = await db.if_rate_coins_for_table()
        lucky_coin_user = await db.coins_user_from_users(str(message.from_user.id))
        try:
            if float(message.text) == int or float and float(message.text) <= float(lucky_coin_user[0][0]):
                await state.update_data(lucky_coin=float(message.text))
                data = await state.get_data()
                lucky_coin = data['lucky_coin']
                await state.set_state(TradeUserCoins.accept_lucky_cash_trade)
                await state.update_data(lucky_coin=lucky_coin)
                await message.answer(
                    f'{lucky_coin} {rate_coin[0][0]} = {round(lucky_coin / rate_coin[0][2], 2)} {rate_coin[0][1]}\n\n'
                    f'<u><b>Вы можете согласиться</b></u> или же нажать <u><b>"Отменить"</b></u> '
                    f'и операция не будет произведена.',
                    reply_markup=create_inline_kb(1, 'assent', last_btn='back_delete'))
            else:
                await message.answer(f'У вас не хватает монет для обмена')
        except ValueError:
            await message.answer(f'Ошибка! Ввести можно только целое либо неполное число!')
    if await state.get_state() == TradeUserCoins.cash_to_chips:
        current_time = datetime.now().isoformat()
        rate_coin = await db.if_rate_coins_for_table()
        cash_coin_user = await db.coins_user_from_users(str(message.from_user.id))
        try:
            if float(message.text) == int or float and float(message.text) <= float(cash_coin_user[0][1]):
                await state.update_data(cash=float(message.text))
                data = await state.get_data()
                cash = data['cash']
                await state.set_state(TradeUserCoins.accept_cash_chips_trade)
                await state.update_data(cash=cash)
                await message.answer(
                    f'{cash} {rate_coin[1][0]} = {round(cash / rate_coin[1][2], 2)} фишек\n\n'
                    f'<u><b>Вы можете согласиться</b></u> или же нажать <u><b>"Отменить"</b></u> '
                    f'и операция не будет произведена.',
                    reply_markup=create_inline_kb(1, 'assent', last_btn='back_delete'))
            else:
                await message.answer(f'У вас не хватает монет для обмена')
        except ValueError:
            await message.answer(f'Ошибка! Ввести можно только целое либо неполное число!')

# Обработчик состояние согласия с операцией обмена
@router.callback_query(F.data == 'assent', StateFilter(*[TradeUserCoins.accept_lucky_cash_trade, TradeUserCoins.accept_cash_chips_trade]))
async def trade_user_coins_assent(callback: CallbackQuery, state: FSMContext):
    current_time = datetime.now().isoformat()
    if await state.get_state() == TradeUserCoins.accept_lucky_cash_trade:
        lucky_coin_user = await db.coins_user_from_users(str(callback.from_user.id))
        nickname = await db.nickname_from_users_where_id(str(callback.from_user.id))
        rate_coin = await db.if_rate_coins_for_table()
        data = await state.get_data()
        lucky_coin = data['lucky_coin']
        lucky_coin_user = float(lucky_coin_user[0][0]) - lucky_coin
        CashOnline = lucky_coin / rate_coin[0][2]
        await db.update_coin_for_user(user_id=str(callback.from_user.id), Lucky_coin=lucky_coin_user,
                                      CashOnline=round(CashOnline, 2))
        await state.clear()
        await callback.message.delete()
        await callback.answer(chat_id=callback.from_user.id, text=f'Успешный обмен')
        await callback.message.answer(LEXICON_RU['start'] + f'\n\n❗<b>Ваш ник - {nickname[0][0]}</b>\n\n'
                             + f'❗<b>Ваш id - {callback.from_user.id}</b>',
                             reply_markup=create_inline_kb(2, 'coins', 'merch',
                                                           'referral', 'Статистика рефералов', 'Получить бонусы'))
        await db.info_user_for_user(callback.from_user.id, current_time)
    if await state.get_state() == TradeUserCoins.accept_cash_chips_trade:
        data = await state.get_data()
        nickname = await db.nickname_from_users_where_id(str(callback.from_user.id))
        cash_coin = data['cash']
        async with aiosqlite.connect('userdata.db') as conn:
            cash = await conn.execute('SELECT CashOnline FROM users WHERE user_id = ?', (callback.from_user.id,))
            cash = await cash.fetchall()
            chips = await conn.execute('SELECT Chips FROM users WHERE user_id = ?', (callback.from_user.id,))
            chips = await chips.fetchall()
            rate_cash_chips = await conn.execute('SELECT rate FROM rate_coins')
            rate_cash_chips = await rate_cash_chips.fetchall()
            print(rate_cash_chips)
            await conn.execute('UPDATE users SET CashOnline = ?, Chips = ? WHERE user_id = ?', (round(cash[0][0] - float(cash_coin), 2), chips[0][0] + round(cash_coin/rate_cash_chips[1][0], 2), callback.from_user.id))
            await conn.commit()
        await callback.message.delete()
        await callback.answer(chat_id=callback.from_user.id, text=f'Успешный обмен')
        await callback.message.answer(LEXICON_RU['start'] + f'\n\n❗<b>Ваш ник - {nickname[0][0]}</b>\n\n'
                             + f'❗<b>Ваш id - {callback.from_user.id}</b>',
                             reply_markup=create_inline_kb(2, 'coins', 'merch',
                                                           'referral', 'Статистика рефералов', 'Получить бонусы'))
        await db.info_user_for_user(callback.from_user.id, current_time)
@router.callback_query(F.data == 'trade_admin')
async def qr_code(callback: CallbackQuery):
    qrcode = await QRCode(callback.from_user.id).code_generate()
    await callback.message.bot.send_photo(chat_id=callback.from_user.id, photo=FSInputFile(f'qr_code_{callback.from_user.id}.png'),
                                          caption='Данный QR вам необходимо показать администратору, чтобы вам выдали фишки')
    os.remove(f'qr_code_{callback.from_user.id}.png')


@router.callback_query(F.data == 'referral')
async def send_referral_link(callback: CallbackQuery):
    user_id = callback.from_user.id
    # Генерируем ссылку на бота с параметром, который содержит user_id
    referral_link = f"https://t.me/Malevin_Cas_bot?start={user_id}"
    await callback.message.answer(f"Ваша реферальная ссылка: {referral_link}")

@router.callback_query(F.data == 'Статистика рефералов')
async def referrals_statistic(callback: CallbackQuery):
    async with aiosqlite.connect('userdata.db') as conn:
        referrals = await conn.execute('SELECT user_id, username, nickname, Lucky, CashOnline, Chips FROM users WHERE referral = ?', (callback.from_user.id,))
        referrals = await referrals.fetchall()
    if referrals == []:
        await callback.message.answer('Вы никого не приглашали.')
    else:
        for i in referrals:
            await callback.message.answer(f'<b>ID</b>: {i[0]}\n'
                                          f'<b>Username</b>: {i[1]}\n'
                                          f'<b>Nick</b>: {i[2]}\n'
                                          f'<b>Количество монет LuckyCash</b>: {i[3]}\n'
                                          f'<b>Количество монет CashOnline</b>: {i[4]}\n'
                                          f'<b>Количество фишек</b>: {i[5]}')

@router.callback_query(F.data == 'Получить бонусы')
async def get_bonus(callback: CallbackQuery):
    web_app_url = f"https://{config.tg_bot.ipv4}:8000/scanbonus?user_id={callback.from_user.id}"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="Cканер",
        url=web_app_url)
    )
    await callback.message.answer("Нажмите кнопку для открытия сканера QR кодов:", reply_markup=builder.as_markup())

page = 0
@router.callback_query(F.data == 'merch')
async def get_products(callback: CallbackQuery):
    global page
    async with aiosqlite.connect('userdata.db') as db:
        products = await db.execute('SELECT * FROM merch')
        products = await products.fetchall()
    if products == []:
        await callback.message.answer('Список товаров пуст')
    else:
        await callback.message.bot.send_photo(chat_id=callback.from_user.id, photo=FSInputFile(products[page][3]), caption=f'<b>ID</b>: {products[page][0]}\n<b>Название</b>: {products[page][1]}\n<b>Цена</b>: {products[page][2]} <b>CashOnline</b>',
                                              reply_markup=create_inline_kb(1, 'Еще ->', 'Купить'))

@router.callback_query(F.data == 'Еще ->')
async def merch(callback: CallbackQuery):
    global page
    page += 1
    await callback.message.delete()
    async with aiosqlite.connect('userdata.db') as db:
        products = await db.execute('SELECT * FROM merch ORDER BY id')
        products = await products.fetchall()
    try:
        await callback.message.bot.send_photo(chat_id=callback.from_user.id, photo=FSInputFile(products[page][3]), caption=f'<b>ID</b>: {products[page][0]}\n<b>Название</b>: {products[page][1]}\n<b>Цена</b>: {products[page][2]} <b>CashOnline</b>',
                                              reply_markup=create_inline_kb(1, 'Еще ->', 'Купить'))
    except IndexError:
        page = 0
        await callback.message.bot.send_photo(chat_id=callback.from_user.id, photo=FSInputFile(products[page][3]), caption=f'<b>ID</b>: {products[page][0]}\n<b>Название</b>: {products[page][1]}\n<b>Цена</b>: {products[page][2]} <b>CashOnline</b>',
                                              reply_markup=create_inline_kb(1, 'Еще ->', 'Купить'))

@router.callback_query(F.data == 'Купить')
async def buy_product(callback: CallbackQuery):
    product_id = callback.message.caption.split('\n')[0].split(' ')[1]
    print(product_id)
    current_time = datetime.now().isoformat()
    await callback.message.delete()
    async with aiosqlite.connect('userdata.db') as conn:
        price = await conn.execute('SELECT price FROM merch ORDER BY id')
        price = await price.fetchall()
        print(price)
        co_user = await conn.execute('SELECT CashOnline FROM users WHERE user_id = ?', (callback.from_user.id,))
        co_user = await co_user.fetchall()
    if price[0][0] > co_user[0][0]:
        await callback.message.answer('У вас недостаточно средств на покупку данной вещи.')
    else:
        async with aiosqlite.connect('userdata.db') as conn:
            await conn.execute('UPDATE users SET CashOnline = ? WHERE user_id = ?', (co_user[0][0] - price[0][0], callback.from_user.id))
            await conn.commit()
        await callback.message.answer('Вы приобрели данную вещь.')
        for i in ast.literal_eval(config.tg_bot.admin_id):
            await callback.message.bot.send_message(chat_id=int(i), text=f'‼️<b>{callback.from_user.id}</b> купил вещь с <b>ID {product_id}</b>‼️')
        await db.info_user_for_user(callback.from_user.id, current_time)

class DoQuiz(StatesGroup):
    answer1 = State()
    answer2 = State()
    answer3 = State()
@router.callback_query(F.data.in_(['Начать решать', 'Отказаться']), StateFilter(None))
async def doing_quiz(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'Начать решать':
        with open('exchange_look_quizzes.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        data = data[0]
        name_quiz = list(data.keys())
        data = data[name_quiz[0]]
        questions = list(data.keys())
        answers = list(data.values())
        answers = answers[:-1]
        random.shuffle(answers)
        await callback.message.answer(text=questions[0], reply_markup=create_inline_kb(1, *answers))
        await state.set_state(DoQuiz.answer1)
    if callback.data == 'Отказаться':
        await callback.message.delete()
        await state.clear()

@router.callback_query(F.data, DoQuiz.answer1)
async def answer_1(callback: CallbackQuery, state: FSMContext):
    await state.update_data(answer1 = callback.data)
    with open('exchange_look_quizzes.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    data = data[0]
    name_quiz = list(data.keys())
    data = data[name_quiz[0]]
    questions = list(data.keys())
    answers = list(data.values())
    answers = answers[:-1]
    random.shuffle(answers)
    await callback.message.answer(text=questions[1], reply_markup=create_inline_kb(1, *answers))
    await state.set_state(DoQuiz.answer2)

@router.callback_query(F.data, DoQuiz.answer2)
async def answer_2(callback: CallbackQuery, state: FSMContext):
    await state.update_data(answer2 = callback.data)
    with open('exchange_look_quizzes.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    data = data[0]
    name_quiz = list(data.keys())
    data = data[name_quiz[0]]
    questions = list(data.keys())
    answers = list(data.values())
    answers = answers[:-1]
    random.shuffle(answers)
    await callback.message.answer(text=questions[2], reply_markup=create_inline_kb(1, *answers))
    await state.set_state(DoQuiz.answer3)

@router.callback_query(F.data, DoQuiz.answer3)
async def answer_3(callback: CallbackQuery, state: FSMContext):
    await state.update_data(answer3 = callback.data)
    with open('exchange_look_quizzes.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    data = data[0]
    name_quiz = list(data.keys())
    data = data[name_quiz[0]]
    answers = list(data.values())
    answers = answers[:-1]
    answers_user = await state.get_data()
    if answers == [answers_user['answer1'], answers_user['answer2'], answers_user['answer3']]:
        await callback.message.answer('Вы правильно решили квиз. Бонус зачислен на ваш счет')
        await db.give_bonus(float(data['награда']), callback.from_user.id)
        async with aiosqlite.connect('userdata.db') as conn:
            await conn.execute('DELETE FROM quizzes')
            await conn.commit()
        await db.info_user_for_user(callback.from_user.id, datetime.now().isoformat())
        await state.clear()
    else:
        await callback.message.answer('К сожалению, вы ошиблись в одном из вопросов. В следующий раз повезет!')
        async with aiosqlite.connect('userdata.db') as conn:
            await conn.execute('DELETE FROM quizzes')
            await conn.commit()
        await state.clear()


async def check_subscription(user_id: int, channel_id: str, bot) -> bool:
    try:
        # Получаем информацию о пользователе в канале
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)

        # Проверяем статус подписки пользователя
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR,
                                 ChatMemberStatus.MEMBER]
    except Exception as e:
        print(f"Ошибка при проверке подписки: {e}")
        return False
@router.callback_query(F.data == 'Проверить')
async def check_subcribe(callback: CallbackQuery):
    channel = callback.message.text.split('\n')[1].split('/')[-1]
    print(channel)
    subscribed = await check_subscription(callback.from_user.id, channel)

    if subscribed:
        await message.answer("Вы подписаны на канал.")
    else:
        await message.answer("Вы не подписаны на канал.")