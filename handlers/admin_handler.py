import ast
import asyncio
import json
import os

import aiosqlite
from aiogram import F, Router, Bot
from aiogram.types import CallbackQuery, Message, FSInputFile, InlineKeyboardButton
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramAPIError
from datetime import datetime

from aiogram.utils.keyboard import InlineKeyboardBuilder

from config_data.config import Config, load_config
from keyboards.inline_keyboard import create_inline_kb
from keyboards.old_message_kb import get_name_keyboard, give_old_message_keyboard
from lexicon.lexicon_ru import LEXICON_RU
from database import database as db
from workers.qr_code import QRCode

# Реализация роутера
router = Router()
config: Config = load_config()


# Реализация класса состояния
class ChangeRateCoins(StatesGroup):
    waiting_choice_rate = State()
    waiting_rate = State()


# Состояние для пойска клиента и базы данных клиентов
class FindUsersForDB(StatesGroup):
    waiting_choice_admin = State()
    waiting_id_user = State()
    append_coins_user = State()
    remove_coins_user = State()
    message_user = State()
    message_admin = State()
    message_old = State()


# Состояние для списывания монет
class RemoveCoinsForUser(StatesGroup):
    lucky_coins = State()
    CashOnline_coins = State()
    OtherCoins_coins = State()
    Chips_coins = State()


# Состояние для начисления монет
class AddCoinsForUser(StatesGroup):
    lucky_coins = State()
    CashOnline_coins = State()
    OtherCoins_coins = State()
    Chips_coins = State()


# Состояние для связи
class ActionLetterForAdmin(StatesGroup):
    message_for_all_users = State()
    old_message = State()
    delete_old_message = State()
    change_old_message = State()
    change_name_old = State()
    change_text_old = State()
    add_old_message = State()
    add_name_old_message = State()
    add_text_old_message = State()


# Состояние для квизов
class ChangeOrGiveQuizzes(StatesGroup):
    append_new_quiz = State()
    append_question_one = State()
    append_question_two = State()
    append_question_three = State()
    append_answer_one = State()
    append_answer_two = State()
    append_answer_three = State()
    append_prize = State()


# Обработка кнопки "Квизы"
@router.callback_query(F.data == 'quizzes')
async def quizzes_admin(callback_query: CallbackQuery):
    await db.info_quizzes_for_quizzes_json()
    await callback_query.message.edit_text(f'Пожалуйста, выберете нужную кнопку:\n\n'
                                           f'- Показать квизы (json-файл со всеми квизами)\n\n'
                                           f'- Редактировать (добавить, изменить, удалить квизы)\n\n'
                                           f'- Отправить всем (каждому клиенту будет отправлен выбранный вами квиз)',
                                           reply_markup=create_inline_kb(2, 'look_quizzes',
                                                                         'change_quizzes', 'give_quizzes_all',
                                                                         last_btn='back'))


# Редактировать квизы
@router.callback_query(F.data == 'change_quizzes')
async def change_quizzes_for_admin(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(ChangeOrGiveQuizzes.append_new_quiz)
    await callback_query.message.edit_text(f'❗Пожалуйста, введите названия для квиза')


# Обработка названия
@router.message(StateFilter(ChangeOrGiveQuizzes.append_new_quiz), F.text)
async def append_new_name(message: Message, state: FSMContext):
    await state.set_state(ChangeOrGiveQuizzes.append_question_one)
    await state.update_data(name_quiz=message.text)
    await message.answer(f'❗Пожалуйста, введите первый вопрос.\n\n'
                         f'Важно, чтобы предложение заканчивалось "?"')


# Обработка первого вопроса
@router.message(StateFilter(ChangeOrGiveQuizzes.append_question_one), F.text)
async def append_new_question_one(message: Message, state: FSMContext):
    if message.text.__contains__('?'):
        await state.update_data(question_one=message.text)
        await message.answer(f'❗Пожалуйста, введите ответ на первый вопрос.')
        await state.set_state(ChangeOrGiveQuizzes.append_answer_one)
    else:
        await message.answer(f'Предложние не заканчивается на "?"')


@router.message(StateFilter(ChangeOrGiveQuizzes.append_answer_one), F.text)
async def append_answer_one(message: Message, state: FSMContext):
    await state.update_data(answer_one=message.text)
    await state.set_state(ChangeOrGiveQuizzes.append_question_two)
    await message.answer('❗Пожалуйста, введите второй вопрос.\n\n'
                         f'Важно, чтобы предложение заканчивалось "?"')


@router.message(StateFilter(ChangeOrGiveQuizzes.append_question_two), F.text)
async def append_new_question_one(message: Message, state: FSMContext):
    if message.text.__contains__('?'):
        await state.update_data(question_two=message.text)
        await message.answer(f'❗Пожалуйста, введите ответ на второй вопрос.')
        await state.set_state(ChangeOrGiveQuizzes.append_answer_two)
    else:
        await message.answer(f'Предложние не заканчивается на "?"')


@router.message(StateFilter(ChangeOrGiveQuizzes.append_answer_two), F.text)
async def append_answer_one(message: Message, state: FSMContext):
    await state.update_data(answer_two=message.text)
    await state.set_state(ChangeOrGiveQuizzes.append_question_three)
    await message.answer('❗Пожалуйста, введите третий вопрос.\n\n'
                         f'Важно, чтобы предложение заканчивалось "?"')


@router.message(StateFilter(ChangeOrGiveQuizzes.append_question_three), F.text)
async def append_new_question_one(message: Message, state: FSMContext):
    if message.text.__contains__('?'):
        await state.update_data(question_three=message.text)
        await message.answer(f'❗Пожалуйста, введите ответ на третий вопрос.')
        await state.set_state(ChangeOrGiveQuizzes.append_answer_three)
    else:
        await message.answer(f'Предложние не заканчивается на "?"')


@router.message(StateFilter(ChangeOrGiveQuizzes.append_answer_three), F.text)
async def append_answer_one(message: Message, state: FSMContext):
    await state.update_data(answer_three=message.text)
    await state.set_state(ChangeOrGiveQuizzes.append_prize)
    await message.answer('❗Пожалуйста, введите количество lucky монет, которое получить клиент.\n\n'
                         f'Важно, чтобы это было либо целлое, либо неполное число.')


@router.message(StateFilter(ChangeOrGiveQuizzes.append_prize), F.text)
async def append_prize(message: Message, state: FSMContext):
    if message.text == int or float:
        await state.update_data(prize=message.text)
        data = await state.get_data()
        name = data['name_quiz']
        question_one = data['question_one']
        question_two = data['question_two']
        question_three = data['question_three']
        answer_one = data['answer_one']
        answer_two = data['answer_two']
        answer_three = data['answer_three']
        prize = data['prize']
        await db.append_new_quizzes(name, question_one, answer_one, question_two, answer_two, question_three,
                                    answer_three, prize)
        await state.clear()
        await db.info_quizzes_for_quizzes_json()
        await message.answer(f'Пожалуйста, выберете нужную кнопку:\n\n'
                             f'- Показать квизы (json-файл со всеми квизами)\n\n'
                             f'- Редактировать (добавить, изменить, удалить квизы)\n\n'
                             f'- Отправить всем (каждому клиенту будет отправлен выбранный вами квиз)',
                             reply_markup=create_inline_kb(2, 'look_quizzes',
                                                           'change_quizzes', 'give_quizzes_all',
                                                           last_btn='back'))
    else:
        await message.answer(f'Введите число или неполное число')


# Показать все квизы
@router.callback_query(F.data == 'look_quizzes')
async def quizzes_admin(callback_query: CallbackQuery):
    await callback_query.message.delete()
    file = FSInputFile('exchange_look_quizzes.json')
    message_text = "JSON-файл для Вас ❤️"
    await callback_query.bot.send_document(chat_id=callback_query.from_user.id, document=file,
                                           caption=message_text)
    await db.info_quizzes_for_quizzes_json()
    await callback_query.message.answer(f'❗Пожалуйста, выберете нужную кнопку:\n\n'
                                        f'- Показать квизы (json-файл со всеми квизами)\n\n'
                                        f'- Редактировать (добавить, изменить, удалить квизы)\n\n'
                                        f'- Отправить всем (каждому клиенту будет отправлен выбранный вами квиз)',
                                        reply_markup=create_inline_kb(2, 'look_quizzes',
                                                                      'change_quizzes', 'give_quizzes_all',
                                                                      last_btn='back'))


@router.callback_query(F.data == 'give_quizzes_all')
async def send_quizzes(callback: CallbackQuery):
    async with aiosqlite.connect('userdata.db') as conn:
        ids = await conn.execute('SELECT user_id FROM users')
        ids = await ids.fetchall()
    for i in ids:
        await callback.message.bot.send_message(chat_id=int(i[0]), text='❗Появился новый квиз! Вы можете решить его и получить вознаграждение❗', reply_markup=create_inline_kb(1,'Начать решать', 'Отказаться'))




# Обработка кнопки "Связь"
@router.callback_query(F.data == 'message')
async def letter_from_admin(callback_query: CallbackQuery):
    await db.info_from_old_message_in_json()
    await callback_query.message.edit_text(f'Пожалуйста, выберете нужную кнопку: \n\n'
                                           f'- Сообщение для всех (Ваше сообщение будет отправлено всем клиентам)\n\n'
                                           f'- Отложенные сообщения (Здесь можно изменить, добавить или удалить '
                                           f'отложенные сообщения)',
                                           reply_markup=create_inline_kb(1, 'message_for_all',
                                                                         'old_messages_change', 'Отложенное сообщение', last_btn='back'))


# Обработки кнопки отложенные сообщения
@router.callback_query(F.data == 'old_messages_change')
async def old_message_change(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text(f'❗Пожалуйста выберете нужную вам кнопку: \n\n'
                                           f'- Добавить (Добавление нового отложенного сообщения)\n\n'
                                           f'- Изменить (Изменить имеющиеся отложенные сообщения)\n\n'
                                           f'- Удалить (Удалить выбранное отложенное сообщение)\n\n'
                                           f'Показать (Посмотреть все отложенные сообщения)',
                                           reply_markup=create_inline_kb(3, 'append_old_message',
                                                                         'change_old_message', 'delete_old_message',
                                                                         'show_old_message', last_btn='back'))
    await state.set_state(ActionLetterForAdmin.old_message)


# Показываем базу данных отложенных сообщений в виде json-файла
@router.callback_query(StateFilter(ActionLetterForAdmin.old_message), F.data == 'show_old_message')
async def show_old_message(callback_query: CallbackQuery, state: FSMContext):
    file = FSInputFile('exchange_data_old.json')
    message_text = "JSON-файл для Вас ❤️"
    await callback_query.bot.send_document(chat_id=callback_query.from_user.id, document=file,
                                           caption=message_text)
    await callback_query.message.delete()
    await callback_query.message.answer(f'❗Пожалуйста выберете нужную вам кнопку: \n\n'
                                        f'- Добавить (Добавление нового отложенного сообщения)\n\n'
                                        f'- Изменить (Изменить имеющиеся отложенные сообщения)\n\n'
                                        f'- Удалить (Удалить выбранное отложенное сообщение)\n\n'
                                        f'- Показать отложенные сообщения (Посмотреть все отложенные сообщения)',
                                        reply_markup=create_inline_kb(3, 'append_old_message',
                                                                      'change_old_message', 'delete_old_message',
                                                                      'show_old_message', last_btn='back'))


# Обрабатываем кнопку удалить отложенные сообщения
@router.callback_query(StateFilter(ActionLetterForAdmin.old_message), F.data == 'delete_old_message')
async def button_delete(callback_query: CallbackQuery, state: FSMContext):
    data_old_message = await db.info_from_old_message()
    name = [x[1] for x in data_old_message]
    await callback_query.message.edit_text(f'Пожалуйста, выберете какой текст вы хотите удалить.\n\n'
                                           f'Кнопки ниже названы точно также, как и названия для отложенного текста.',
                                           reply_markup=get_name_keyboard(name, last_btn='back'))
    await state.set_state(ActionLetterForAdmin.delete_old_message)


# Удаляем отложенное сообщение
@router.callback_query(StateFilter(ActionLetterForAdmin.delete_old_message), F.data.contains('Текст - '))
async def delete_old_message(callback_query: CallbackQuery, state: FSMContext):
    name_old_message = callback_query.data.replace('Текст - ', '')
    await db.delete_old_message(name_old_message)
    await state.clear()
    await callback_query.bot.answer_callback_query(callback_query.id, f'Отложенное сообщение удалено')
    await db.info_from_old_message_in_json()
    await callback_query.message.edit_text(f'❗Пожалуйста выберете нужную вам кнопку: \n\n'
                                           f'- Добавить (Добавление нового отложенного сообщения)\n\n'
                                           f'- Изменить (Изменить имеющиеся отложенные сообщения)\n\n'
                                           f'- Удалить (Удалить выбранное отложенное сообщение)\n\n'
                                           f'Показать (Посмотреть все отложенные сообщения)',
                                           reply_markup=create_inline_kb(3, 'append_old_message',
                                                                         'change_old_message', 'delete_old_message',
                                                                         'show_old_message', last_btn='back'))
    await state.set_state(ActionLetterForAdmin.old_message)


# Обрабатываем кнопку изменить отложенные сообщения
@router.callback_query(StateFilter(ActionLetterForAdmin.old_message), F.data == 'change_old_message')
async def change_old_message(callback_query: CallbackQuery, state: FSMContext):
    data_old_message = await db.info_from_old_message()
    name = [x[1] for x in data_old_message]
    await callback_query.message.edit_text(f'Пожалуйста, выберете какой текст вы хотите изменить.\n\n'
                                           f'Кнопки ниже названы точно также, как и названия для отложенного текста.',
                                           reply_markup=get_name_keyboard(name, last_btn='back'))
    await state.set_state(ActionLetterForAdmin.change_old_message)


# Обработка изменение выбранного отложенного сообщения
@router.callback_query(StateFilter(ActionLetterForAdmin.change_old_message), F.data.contains('Текст - '))
async def choice_old_message(callback_query: CallbackQuery, state: FSMContext):
    name_old_message = callback_query.data.replace('Текст - ', '')
    await state.update_data(name_old_message=name_old_message)
    await callback_query.message.edit_text(f'Вы хотите поменять название или содержание отложенного сообщения?\n\n'
                                           f'❗Пожалуйста, сделать Ваш выбор.',
                                           reply_markup=create_inline_kb(2, 'change_name_old',
                                                                         'change_text_old', last_btn='back'))


# Меняем текст отложенного сообщения
@router.callback_query(StateFilter(ActionLetterForAdmin.change_old_message), F.data == 'change_text_old')
async def change_text_old(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(ActionLetterForAdmin.change_text_old)
    data = await state.get_data()
    name = data['name_old_message']
    text = await db.info_old_message_for_name(name)
    await callback_query.message.edit_text(f'❗На данный момент отложенное сообщение под названием <b>{name}</b> '
                                           f'имеет текс: \n\n'
                                           f'{text[0]}\n\n'
                                           f'❗Пожалуйста, напишите новый текст для отложенного сообщения, напоминаем, '
                                           f'что он должен быть понятным и содержательным.',
                                           reply_markup=create_inline_kb(1, last_btn='back'))
    await state.update_data(name_old_message=name)


# Обрабатываем текст для отложенного сообщения
@router.message(StateFilter(ActionLetterForAdmin.change_text_old), F.text)
async def new_text_old(message: Message, state: FSMContext):
    new_text = message.text
    data = await state.get_data()
    name = data['name_old_message']
    await db.change_old_message(name_old_message=name, text_old_message=new_text)
    await message.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
    await state.clear()
    await db.info_from_old_message_in_json()
    await message.answer(f'❗Вы успешно сменили текст')
    await message.answer(f'❗Пожалуйста выберете нужную вам кнопку: \n\n'
                         f'- Добавить (Добавление нового отложенного сообщения)\n\n'
                         f'- Изменить (Изменить имеющиеся отложенные сообщения)\n\n'
                         f'- Удалить (Удалить выбранное отложенное сообщение)\n\n'
                         f'- Показать отложенные сообщения (Посмотреть все отложенные сообщения)',
                         reply_markup=create_inline_kb(3, 'append_old_message',
                                                       'change_old_message', 'delete_old_message',
                                                       'show_old_message', last_btn='back'))
    await state.set_state(ActionLetterForAdmin.old_message)


# Меняем имя отложенного сообщения
@router.callback_query(StateFilter(ActionLetterForAdmin.change_old_message), F.data == 'change_name_old')
async def change_name_old(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(ActionLetterForAdmin.change_name_old)
    data = await state.get_data()
    name = data['name_old_message']
    await callback_query.message.edit_text(f'❗На данный момент отложенное сообщение имеет название: \n\n'
                                           f'- {name}\n\n'
                                           f'Пожалуйста, напишите новое название, напоминаем, '
                                           f'что оно должно быть понятным и содержательным.',
                                           reply_markup=create_inline_kb(1, last_btn='back'))
    await state.update_data(name_old_message=name)


# Обрабатываем имя нового отложенного сообщения
@router.message(StateFilter(ActionLetterForAdmin.change_name_old), F.text)
async def new_name_old(message: Message, state: FSMContext):
    new_name = message.text
    data = await state.get_data()
    name_old_message = data['name_old_message']
    await db.change_old_message(new_name_old_message=new_name, name_old_message=name_old_message)
    await message.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
    await state.clear()
    await db.info_from_old_message_in_json()
    await message.answer(f'❗Вы успешно сменили название')
    await message.answer(f'❗Пожалуйста выберете нужную вам кнопку: \n\n'
                         f'- Добавить (Добавление нового отложенного сообщения)\n\n'
                         f'- Изменить (Изменить имеющиеся отложенные сообщения)\n\n'
                         f'- Удалить (Удалить выбранное отложенное сообщение)\n\n'
                         f'- Показать отложенные сообщения (Посмотреть все отложенные сообщения)',
                         reply_markup=create_inline_kb(3, 'append_old_message',
                                                       'change_old_message', 'delete_old_message',
                                                       'show_old_message', last_btn='back'))
    await state.set_state(ActionLetterForAdmin.old_message)


# Добавление нового отложенного сообщения
@router.callback_query(StateFilter(ActionLetterForAdmin.old_message), F.data == 'append_old_message')
async def append_old_message(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text(f'❗Пожалуйста введите название для отложенного сообщение, например:\n\n'
                                           f'- Новый курс\n\n'
                                           f'- Новые квизы\n\n'
                                           f'Учитываете, что название должно быть понятно Вам, чтобы в дальнейшим '
                                           f'не перепутать его с другим.',
                                           reply_markup=create_inline_kb(1, last_btn='back'))
    await state.set_state(ActionLetterForAdmin.add_name_old_message)


# Обработка названия для отложенного сообщения
@router.message(StateFilter(ActionLetterForAdmin.add_name_old_message), F.text)
async def append_name_old_message(message: Message, state: FSMContext):
    await state.update_data(name_old_message=message.text)
    await message.answer(f'Теперь напишите текст, который Вы хотите отложить на потом под этим названием.\n\n'
                         f'Если Вы допустили ошибку, то ничего страшного. Вы всегда сможете изменить текст в меню')
    await state.set_state(ActionLetterForAdmin.add_text_old_message)


# обработка текст и отправка с названием в дб
@router.message(StateFilter(ActionLetterForAdmin.add_text_old_message), F.text)
async def append_text_old_message(message: Message, state: FSMContext):
    await state.update_data(text_old_message=message.text)
    data = await state.get_data()
    name = data['name_old_message']
    text = data['text_old_message']
    await db.append_new_old_message(name, text)
    await message.answer(f'Отложенное сообщение успешно сохранено')
    await state.clear()
    await db.info_from_old_message_in_json()
    await message.answer(f'Пожалуйста, выберете нужную кнопку: \n\n'
                         f'- Сообщение для всех (Ваше сообщение будет отправлено всем клиентам)\n\n'
                         f'- Отложенные сообщения (Здесь можно изменить, добавить или удалить '
                         f'отложенные сообщения)',
                         reply_markup=create_inline_kb(1, 'message_for_all',
                                                       'old_messages_change', last_btn='back'))


# Сообщение для всех пользователей
@router.callback_query(F.data == 'message_for_all')
async def letter_for_all_users(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text(f'Вы хотите отправить своё сообщение или же отложенное ранее?\n\n'
                                           f'❗Пожалуйста, выберете нужную кнопку ниже',
                                           reply_markup=create_inline_kb(1, 'admin_text', 'old_messages',
                                                                         last_btn='back'))
    await state.set_state(ActionLetterForAdmin.message_for_all_users)


# Обработка отложенного текста для всех клиентов
@router.callback_query(StateFilter(ActionLetterForAdmin.message_for_all_users), F.data == 'old_messages')
async def old_message_for_all_users(callback_query: CallbackQuery, state: FSMContext):
    data_old_message = await db.info_from_old_message()
    name = [x[1] for x in data_old_message]
    await callback_query.message.edit_text(f'Пожалуйста, выберете какой текст вы хотите отправить.\n\n'
                                           f'Кнопки ниже названы точно также, как и названия для отложенного текста.\n\n'
                                           f'❗Напоминаем, что сообщение будет отправлено все клиентам.',
                                           reply_markup=give_old_message_keyboard(name, last_btn='back'))


# Отправляем отложенное сообщение всем клиентам
@router.callback_query(StateFilter(ActionLetterForAdmin.message_for_all_users), F.data.contains('Отправить '))
async def change_message_for_all_users(callback_query: CallbackQuery, state: FSMContext):
    name = callback_query.data.replace('Отправить ', '')
    text = await db.info_old_message_for_name(name)
    await callback_query.message.edit_text(f'❗Текст под названием {name}, c таким содержанием:\n\n'
                                           f'{text[0]}\n\n'
                                           f'❗Вы можете согласиться, тем самым отправив сообщение всем клиентам, '
                                           f'или же вернуться назад.',
                                           reply_markup=create_inline_kb(2, 'accept_old_message',
                                                                         last_btn='back_user'))
    await state.update_data(text=text)


# Обрабатываем согласие на отправку отложенного сообщения всем клиентам
@router.callback_query(StateFilter(ActionLetterForAdmin.message_for_all_users), F.data == 'accept_old_message')
async def give_old_message_for_all_users(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = data['text']
    await callback_query.message.delete()
    all_user_id = await db.user_id_from_users()
    for user_id in all_user_id:
        try:
            await callback_query.bot.send_message(chat_id=user_id[0],
                                                  text=f'❗Сообщение ниже отправлено администрацией\n\n'
                                                       + text[0])
        except TelegramAPIError as e:
            if "Forbidden: bot was blocked by the user" in str(e):
                pass

    await callback_query.message.answer(f'❗Сообщение было успешно отправлено')
    await state.clear()
    await callback_query.message.answer(LEXICON_RU['admin_start'],
                         reply_markup=create_inline_kb(2, 'coin_rate', 'Merch_Showcase',
                                                       'clients', 'quizzes', 'message', 'Сгенерировать QR',
                                                       'Посмотреть рефералов'))


# Обработка своего текста для всех клиентов
@router.callback_query(StateFilter(ActionLetterForAdmin.message_for_all_users), F.data == 'admin_text')
async def admin_text_for_all_users(callback_query: CallbackQuery):
    await callback_query.message.edit_text(f'Пожалуйста, введите текст, который будет отправлен всем.\n\n'
                                           f'❗Напоминаем, что текст нельзя будет поменять, поэтому будет внимательны.',
                                           reply_markup=create_inline_kb(1, last_btn='back'))


# Обработка своего текста для всех клиентов
@router.message(StateFilter(ActionLetterForAdmin.message_for_all_users), F.text)
async def process_delivery_message_for_all_users(message: Message, state: FSMContext):
    text_admin = message.text
    all_user_id = await db.user_id_from_users()
    for user_id in all_user_id:
        try:
            await message.bot.send_message(chat_id=user_id[0], text=f'❗Сообщение ниже отправлено администрацией\n\n'
                                                                    + text_admin)
        except TelegramAPIError as e:
            if "Forbidden: bot was blocked by the user" in str(e):
                pass
    await message.answer(f'❗Сообщение было успешно отправлено')
    await state.clear()
    await message.answer(LEXICON_RU['admin_start'],
                         reply_markup=create_inline_kb(2, 'coin_rate', 'Merch_Showcase',
                                                       'clients', 'quizzes', 'message', 'Сгенерировать QR',
                                                       'Посмотреть рефералов'))


# Показ курса
@router.callback_query(F.data == 'coin_rate')
async def coin_rate_change(callback: CallbackQuery):
    rate_coin = await db.if_rate_coins_for_table()
    await callback.message.edit_text(f'Курс на данный момент: \n\n'
                                     f'Одна монета {rate_coin[0][1]} стоит {rate_coin[0][2]} {rate_coin[0][0]}\n'
                                     f'Одна монета {rate_coin[1][1]} стоит {rate_coin[1][2]} {rate_coin[1][0]}\n',
                                     reply_markup=create_inline_kb(1, 'rate_change',
                                                                   last_btn='back'))


# Выбор курса на изменение
@router.callback_query(F.data == 'rate_change')
async def rate_change_change(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ChangeRateCoins.waiting_choice_rate)
    rate_coin = await db.if_rate_coins_for_table()
    await callback.message.edit_text(f'Какой курс Вы хотите поменять? \n\n'
                                     f'1. Одна монета {rate_coin[0][1]} стоит {rate_coin[0][2]} {rate_coin[0][0]}\n\n'
                                     f'2. Одна монета {rate_coin[1][1]} стоит {rate_coin[1][2]} {rate_coin[1][0]}\n',
                                     reply_markup=create_inline_kb(2, '1', '2', last_btn='back'))


# Ожидание нового курса от админа
@router.callback_query(StateFilter(ChangeRateCoins.waiting_choice_rate), F.data == '1')
async def append_rate_1_to_rate_tabl1(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(f'Пожалуйста, впишите нужный курс. \n\n'
                                     f'Вписать можно: \n\n'
                                     f'- <b>целые</b> (1; 2; 3; 4)\n\n'
                                     f'- <b>неполные</b> (1,24 ; 2,21; 2,53.',
                                     reply_markup=create_inline_kb(1, last_btn='back_delete'))
    await state.update_data(id_coins=float(callback.data))
    await state.set_state(ChangeRateCoins.waiting_rate)


@router.callback_query(StateFilter(ChangeRateCoins.waiting_choice_rate), F.data == '2')
async def append_rate_1_to_rate_tabl1(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(f'Пожалуйста, впишите нужный курс. \n\n'
                                     f'Вписать можно: \n\n'
                                     f'- <b>целые</b> (1; 2; 3; 4)\n\n'
                                     f'- <b>неполные</b> (1.24 ; 2.21; 2.53.',
                                     reply_markup=create_inline_kb(1, last_btn='back_delete'))
    await state.update_data(id_coins=float(callback.data))
    await state.set_state(ChangeRateCoins.waiting_rate)


# Сохранение курса
@router.message(StateFilter(ChangeRateCoins.waiting_rate), F.text)
async def append_rate_to_rate_tabl(message: Message, state: FSMContext):
    current_time = datetime.now().isoformat()
    try:
        if float(message.text) == int or float:
            await state.update_data(rate=float(message.text))
            data = await state.get_data()
            rate = data['rate']
            id_coins = data['id_coins']
            await db.change_rate_coins_for_table_rate(rate, id_coins)
            await message.bot.send_message(chat_id=message.chat.id, text=f'Курс успешно зарегистрирован')
            await state.clear()
            await message.answer(LEXICON_RU['admin_start'],
                                 reply_markup=create_inline_kb(2, 'coin_rate', 'Merch_Showcase',
                                                               'clients', 'quizzes', 'message', 'Сгенерировать QR',
                                                               'Посмотреть рефералов'))
    except ValueError:
        await message.answer(f'Ошибка! Ввести можно только целое либо неполное число!')


# Поиск пользователей
@router.callback_query(F.data == 'clients')
async def client_base(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FindUsersForDB.waiting_choice_admin)
    await callback.message.edit_text(f'❗Пожалуйста выберете нужную кнопку❗\n\n'
                                     f'- Знаю id клиента (Нужно будет вбить id клиента, который можно узнать либо '
                                     f'у самого клиента в профиле, либо посмотреть в базе клиентов)\n\n'
                                     f'- База клиентов (Показать всех клиентов. Важно! Вам придёт <b>JSON-файл</b>)\n\n'
                                     f'- Вернуться назад (Отменить действие)',
                                     reply_markup=create_inline_kb(2, 'base_user', 'id_seek',
                                                                   last_btn='back'))


# Функция для отправки JSON файла в чат
@router.callback_query(StateFilter(FindUsersForDB.waiting_choice_admin), F.data == 'base_user')
async def show_base_user(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    async with aiosqlite.connect('userdata.db') as conn:
        data = await conn.execute('SELECT * FROM users')
        data = await data.fetchall()
    exchange_data = []
    for row in data:
        exchange_data.append({
            "id": row[0],
            "username": row[1],
            "nickname": row[2],
            "Lucky": row[3],
            "CashOnline": row[4],
            "OtherCoins": row[5],
            "Chips": row[6],
            "referral": row[7],
            "current_time": datetime.now().isoformat()
        })
    with open('all_users.json', 'w', encoding='utf-8') as json_file:
        json.dump(exchange_data, json_file, ensure_ascii=False, indent=4)
    file = FSInputFile("all_users.json")
    message_text = "JSON-файл для вас ❤️"
    # Отправляем JSON-файл как документ в ответ на инлайн запрос
    await callback.bot.send_document(chat_id=callback.from_user.id, document=file,
                                     caption=message_text)
    await callback.message.delete()
    await state.set_state(FindUsersForDB.waiting_choice_admin)
    await callback.message.answer(f'❗Пожалуйста выберете нужную кнопку❗\n\n'
                                  f'- Знаю id клиента (Нужно будет вбить id клиента, который можно узнать либо '
                                  f'у самого клиента в профиле, либо посмотреть в базе клиентов)\n\n'
                                  f'- База клиентов (Показать всех клиентов. Важно! Вам придёт <b>JSON-файл</b>)\n\n'
                                  f'- Вернуться назад (Отменить действие)',
                                  reply_markup=create_inline_kb(2, 'base_user', 'id_seek',
                                                                last_btn='back'))


# Обрабатываем 'поиск по id'
@router.callback_query(StateFilter(FindUsersForDB.waiting_choice_admin), F.data == 'id_seek')
async def id_seek_for_user_db(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FindUsersForDB.waiting_id_user)
    await callback.message.edit_text(f'Пожалуйста, введите id Клиента:\n\n'
                                     f'❗Только цифры, например "245648012"',
                                     reply_markup=create_inline_kb(1, last_btn='back_delete'))


# Поиск по id, машина состояния
@router.message(StateFilter(FindUsersForDB.waiting_id_user), F.text)
async def id_user_showing(message: Message, state: FSMContext):
    await state.update_data(user_id=message.text)
    data = await state.get_data()
    user_id = data['user_id']
    user_info = await db.show_info_by_id_for_users(user_id)
    if user_info is not None:
        await message.answer(f'❗Информация по данному пользователю\n\n'
                             f'id - {user_info[0]}\n'
                             f'username - @{user_info[1]}\n'
                             f'nickname - {user_info[2]}\n'
                             f'Lucky - {user_info[3]}\n'
                             f'CashOnline - {user_info[4]}\n'
                             f'OtherCoins - {user_info[5]}\n'
                             f'Chips - {user_info[6]}\n'
                             f'referall - {user_info[7]}\n'
                             f'Время регистрации - {user_info[8]}\n',
                             reply_markup=create_inline_kb(2, 'take_coins', 'add_coins', 'give_message',
                                                           last_btn='back'))
        await state.update_data(user_id=user_id)
    else:
        await message.answer('Ошибка! Такого пользователя не существует.')


# Обработка кнопки сообщения
@router.callback_query(StateFilter(FindUsersForDB.waiting_id_user), F.data == 'give_message')
async def give_message_for_user(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    await state.set_state(FindUsersForDB.message_user)
    await callback.message.edit_text(f'Пожалуйста, выберете нужную кнопку:\n\n'
                                     f'- Свой текст\n\n'
                                     f'- Отложенные сообщения\n\n'
                                     f'❗Напоминаю, что сообщение будет отправлено клиенту с id {user_id}',
                                     reply_markup=create_inline_kb(1, 'admin_text', 'old_messages',
                                                                   last_btn='back_user'))
    await state.update_data(user_id=user_id)


# Оправляем отложенный текст лично клиенту
@router.callback_query(StateFilter(FindUsersForDB.message_user), F.data == 'old_messages')
async def old_message_for_user(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(FindUsersForDB.message_old)
    data_old_message = await db.info_from_old_message()
    name = [x[1] for x in data_old_message]
    data = await state.get_data()
    user_id = data['user_id']
    await callback_query.message.edit_text(f'Пожалуйста, выберете какой текст вы хотите отправить.\n\n'
                                           f'Кнопки ниже названы точно также, как и названия для отложенного текста.\n\n'
                                           f'❗Напоминаем, что id клиента - {user_id}',
                                           reply_markup=give_old_message_keyboard(name, last_btn='back'))
    await state.update_data(user_id=user_id, name_old=name)


# Обрабатываем сообщение
@router.callback_query(StateFilter(FindUsersForDB.message_old), F.data.contains('Отправить '))
async def choice_old_message_for_user(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    name = callback_query.data.replace('Отправить ', '')
    user_id = data['user_id']
    text = await db.info_old_message_for_name(name)
    await callback_query.message.edit_text(f'❗Текст под названием {name}, c таким содержанием:\n\n'
                                           f'{text[0]}\n\n'
                                           f'❗Вы можете согласиться, тем самым отправив сообщение клиенту {user_id}, '
                                           f'или же вернуться назад.',
                                           reply_markup=create_inline_kb(2, 'give_old_message',
                                                                         last_btn='back_user'))
    await state.update_data(user_id=user_id, text=text)


# Отправляем отложенное сообщение клиенту
@router.callback_query(StateFilter(FindUsersForDB.message_old), F.data == 'give_old_message')
async def give_old_message_for_user(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    text = data['text']
    user_info = await db.show_info_by_id_for_users(user_id)
    await callback_query.message.delete()
    try:
        await callback_query.bot.send_message(chat_id=user_id, text=f'❗Сообщение ниже отправлено администрацией\n\n'
                                                                    + text[0])
        await callback_query.message.answer(f'❗Сообщение было успешно отправлено')

    except TelegramAPIError as e:
        if "Forbidden: bot was blocked by the user" in str(e):
            await callback_query.message.answer(f'❗️К сожалению, клиент забанил бота')

    await callback_query.message.answer(f'❗Информация по данному пользователю\n\n'
                                        f'id - {user_info[0]}\n'
                                        f'username - @{user_info[1]}\n'
                                        f'nickname - {user_info[2]}\n'
                                        f'Lucky - {user_info[3]}\n'
                                        f'CashOnline - {user_info[4]}\n'
                                        f'OtherCoins - {user_info[5]}\n'
                                        f'Chips - {user_info[6]}\n'
                                        f'referall - {user_info[7]}\n'
                                        f'Время регистрации - {user_info[8]}\n',
                                        reply_markup=create_inline_kb(2, 'take_coins', 'add_coins', 'give_message',
                                                                      last_btn='back'))

    await state.update_data(user_id=user_id)
    await state.set_state(FindUsersForDB.waiting_id_user)


# Обработка кнопки 'Свой текст'
@router.callback_query(StateFilter(FindUsersForDB.message_user), F.data == 'admin_text')
async def admin_text_for_user(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    await state.set_state(FindUsersForDB.message_admin)
    await callback.message.edit_text(f'Пожалуйста напишите сообщение, которое будет отправлено клиенту.\n\n'
                                     f'❗Напоминаем, что id клиента - {user_id}',
                                     reply_markup=create_inline_kb(1, last_btn='back_user'))
    await state.update_data(user_id=user_id)


# Обработка текст от админа
@router.message(StateFilter(FindUsersForDB.message_admin), F.text)
async def admin_text_editor(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    user_info = await db.show_info_by_id_for_users(user_id)
    text_admin = message.text
    try:
        await message.bot.send_message(chat_id=user_id, text=f'❗Сообщение ниже отправлено администрацией\n\n'
                                                             + text_admin)
        await message.answer(f'❗Сообщение было успешно отправлено')

    except TelegramAPIError as e:
        if "Forbidden: bot was blocked by the user" in str(e):
            await message.answer(f'❗️К сожалению, клиент забанил бота')

    await message.answer(f'❗Информация по данному пользователю\n\n'
                         f'id - {user_info[0]}\n'
                         f'username - @{user_info[1]}\n'
                         f'nickname - {user_info[2]}\n'
                         f'Lucky - {user_info[3]}\n'
                         f'CashOnline - {user_info[4]}\n'
                         f'OtherCoins - {user_info[5]}\n'
                         f'Chips - {user_info[6]}\n'
                         f'referall - {user_info[7]}\n'
                         f'Время регистрации - {user_info[8]}\n',
                         reply_markup=create_inline_kb(2, 'take_coins', 'add_coins', 'give_message',
                                                       last_btn='back'))
    await state.update_data(user_id=user_id)
    await state.set_state(FindUsersForDB.waiting_id_user)


# Обработка кнопки начислить
@router.callback_query(StateFilter(FindUsersForDB.waiting_id_user), F.data == 'add_coins')
async def add_coins_user(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    user_info = await db.show_info_by_id_for_users(user_id)
    await callback.message.edit_text(f'Пожалуйста, выберете монеты для начисления:\n\n'
                                     f'Lucky - {user_info[3]}\n'
                                     f'CashOnline - {user_info[4]}\n'
                                     f'OtherCoins - {user_info[5]}\n'
                                     f'Chips - {user_info[6]}\n\n'
                                     f'❗Напоминаем❗\n\n'
                                     f'id клиента - {user_info[0]}\n'
                                     f'username - {user_info[1]}\n'
                                     f'nickname - {user_info[2]}\n',
                                     reply_markup=create_inline_kb(2, 'Lucky', 'CashOnline',
                                                                   'OtherCoins', 'Chips', last_btn='back_user'))
    await state.update_data(user_id=user_id)
    await state.set_state(FindUsersForDB.append_coins_user)


# Обработка выбора монеты для начисления
@router.callback_query(StateFilter(FindUsersForDB.append_coins_user),
                       (F.data == 'Lucky') | (F.data == 'CashOnline') | (F.data == 'OtherCoins') | (F.data == 'Chips'))
async def append_coins_user(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    user_info = await db.show_info_by_id_for_users(user_id)
    if callback.data == 'Lucky':
        await callback.message.edit_text(f'Клиент {user_info[0]}\n\n'
                                         f'Количество монет lucky - {user_info[3]}\n\n'
                                         f'Введите число монет, которое нужно будет начислить.\n\n'
                                         f'❗Только целые и неполные числа❗',
                                         reply_markup=create_inline_kb(1, last_btn='back_delete'))
        await state.update_data(user_info=user_info)
        await state.set_state(AddCoinsForUser.lucky_coins)

    elif callback.data == 'CashOnline':
        await callback.message.edit_text(f'Клиент {user_info[0]}\n\n'
                                         f'Количество монет CashOnline - {user_info[4]}\n\n'
                                         f'Введите число монет, которое нужно будет начислить.\n\n'
                                         f'❗Только целые и неполные числа❗',
                                         reply_markup=create_inline_kb(1, last_btn='back_delete'))
        await state.update_data(user_info=user_info)
        await state.set_state(AddCoinsForUser.CashOnline_coins)

    elif callback.data == 'OtherCoins':
        await callback.message.edit_text(f'Клиент {user_info[0]}\n\n'
                                         f'Количество монет OtherCoins - {user_info[5]}\n\n'
                                         f'Введите число монет, которое нужно будет начислить.\n\n'
                                         f'❗Только целые и неполные числа❗',
                                         reply_markup=create_inline_kb(1, last_btn='back_delete'))
        await state.update_data(user_info=user_info)
        await state.set_state(AddCoinsForUser.OtherCoins_coins)

    elif callback.data == 'Chips':
        await callback.message.edit_text(f'Клиент {user_info[0]}\n\n'
                                         f'Количество монет Chips - {user_info[6]}\n\n'
                                         f'Введите число монет, которое нужно будет начислить.\n\n'
                                         f'❗Только целые и неполные числа❗',
                                         reply_markup=create_inline_kb(1, last_btn='back_delete'))
        await state.update_data(user_info=user_info)
        await state.set_state(AddCoinsForUser.Chips_coins)


# Получение от пользователя числа монеты для начисления
@router.message(StateFilter(AddCoinsForUser.lucky_coins, AddCoinsForUser.CashOnline_coins,
                            AddCoinsForUser.OtherCoins_coins, AddCoinsForUser.Chips_coins), F.text)
async def append_coins_for_user(message: Message, state: FSMContext):
    data = await state.get_data()
    user_info = data['user_info']
    user_id = user_info[0]
    try:
        # Работаем с lucky
        if await state.get_state() == AddCoinsForUser.lucky_coins:
            new_lucky_coins = user_info[3] + float(message.text)
            await state.update_data(new_lucky_coins=new_lucky_coins, user_id=user_id)
            await message.answer(f'❗Пожалуйста подтвердите операцию❗\n\n'
                                 f'После подтверждения счёт {user_id}, будет выглядеть так:\n\n'
                                 f'lucky - {new_lucky_coins}\n\n'
                                 f'Напоминаем, баланс до начисления:\n\n'
                                 f'lucky - {user_info[3]}',
                                 reply_markup=create_inline_kb(1, 'append_accept_lucky',
                                                               last_btn='back_user'))

        # Работаем с CashOnline
        elif await state.get_state() == AddCoinsForUser.CashOnline_coins:
            new_coins_ChashOnline = user_info[4] + float(message.text)
            await state.update_data(new_coins_ChashOnline=new_coins_ChashOnline, user_id=user_id)
            await message.answer(f'❗Пожалуйста подтвердите операцию❗\n\n'
                                 f'После подтверждения счёт {user_id}, будет выглядеть так:\n\n'
                                 f'CashOnline - {new_coins_ChashOnline}\n\n'
                                 f'Напоминаем, баланс до начисления:\n\n'
                                 f'CashOnline - {user_info[4]}',
                                 reply_markup=create_inline_kb(1, 'append_accept_CashOline',
                                                               last_btn='back_user'))

        # Работаем с OtherCoins
        elif await state.get_state() == AddCoinsForUser.OtherCoins_coins:
            new_coins_OtherCoins = user_info[5] + float(message.text)
            await state.update_data(new_coins_OtherCoins=new_coins_OtherCoins, user_id=user_id)
            await message.answer(f'❗Пожалуйста подтвердите операцию❗\n\n'
                                 f'После подтверждения счёт {user_id}, будет выглядеть так:\n\n'
                                 f'OtherCoins - {new_coins_OtherCoins}\n\n'
                                 f'Напоминаем, баланс до начисления:\n\n'
                                 f'OtherCoins - {user_info[5]}',
                                 reply_markup=create_inline_kb(1, 'append_accept_OtherCoins',
                                                               last_btn='back_user'))

        # Работаем с фишками (Chips)
        elif await state.get_state() == AddCoinsForUser.Chips_coins:
            new_coins_Chips = user_info[6] + float(message.text)
            await state.update_data(new_coins_Chips=new_coins_Chips, user_id=user_id)
            await message.answer(f'❗Пожалуйста подтвердите операцию❗\n\n'
                                 f'После подтверждения счёт {user_id}, будет выглядеть так:\n\n'
                                 f'Chips - {new_coins_Chips}\n\n'
                                 f'Напоминаем, баланс до начисления:\n\n'
                                 f'Chips - {user_info[6]}',
                                 reply_markup=create_inline_kb(1, 'append_accept_Chips',
                                                               last_btn='back_user'))
    except ValueError:
        await message.answer(f'Ошибка! Пожалуйста выберете нужную вам кнопку')


# Обработка начисления lucky
@router.callback_query(StateFilter(AddCoinsForUser.lucky_coins), F.data == 'append_accept_lucky')
async def append_accept_lucky(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    new_lucky_coins = data['new_lucky_coins']
    await db.update_coins_admin_from_user_table(user_id=str(user_id), lucky=new_lucky_coins)
    user_info = await db.show_info_by_id_for_users(user_id)
    await callback.message.edit_text(f'❗Информация по данному пользователю\n\n'
                                     f'id - {user_info[0]}\n'
                                     f'username - {user_info[1]}\n'
                                     f'nickname - {user_info[2]}\n'
                                     f'Lucky - {user_info[3]}\n'
                                     f'CashOnline - {user_info[4]}\n'
                                     f'OtherCoins - {user_info[5]}\n'
                                     f'Chips - {user_info[6]}\n'
                                     f'referall - {user_info[7]}\n'
                                     f'Время регистрации - {user_info[8]}\n',
                                     reply_markup=create_inline_kb(2, 'take_coins',
                                                                   'add_coins', 'give_message', last_btn='back'))
    await state.update_data(user_id=user_id)
    await state.set_state(FindUsersForDB.waiting_id_user)


# Обработка начисления CashOnline
@router.callback_query(StateFilter(AddCoinsForUser.CashOnline_coins), F.data == 'append_accept_CashOline')
async def append_accept_CashOline(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    new_coins_ChashOnline = data['new_coins_ChashOnline']
    await db.update_coins_admin_from_user_table(user_id=str(user_id), CashOnline=new_coins_ChashOnline)
    user_info = await db.show_info_by_id_for_users(user_id)
    await callback_query.message.edit_text(f'❗Информация по данному пользователю\n\n'
                                           f'id - {user_info[0]}\n'
                                           f'username - {user_info[1]}\n'
                                           f'nickname - {user_info[2]}\n'
                                           f'Lucky - {user_info[3]}\n'
                                           f'CashOnline - {user_info[4]}\n'
                                           f'OtherCoins - {user_info[5]}\n'
                                           f'Chips - {user_info[6]}\n'
                                           f'referall - {user_info[7]}\n'
                                           f'Время регистрации - {user_info[8]}\n',
                                           reply_markup=create_inline_kb(2, 'take_coins',
                                                                         'add_coins', 'give_message', last_btn='back'))
    await state.update_data(user_id=user_id)
    await state.set_state(FindUsersForDB.waiting_id_user)


# Обработка начисления OtherCoins
@router.callback_query(StateFilter(AddCoinsForUser.OtherCoins_coins), F.data == 'append_accept_OtherCoins')
async def append_accept_OtherCoin(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    new_coins_OtherCoins = data['new_coins_OtherCoins']
    await db.update_coins_admin_from_user_table(user_id=str(user_id), OtherCoins=new_coins_OtherCoins)
    user_info = await db.show_info_by_id_for_users(user_id)
    await callback_query.message.edit_text(f'❗Информация по данному пользователю\n\n'
                                           f'id - {user_info[0]}\n'
                                           f'username - {user_info[1]}\n'
                                           f'nickname - {user_info[2]}\n'
                                           f'Lucky - {user_info[3]}\n'
                                           f'CashOnline - {user_info[4]}\n'
                                           f'OtherCoins - {user_info[5]}\n'
                                           f'Chips - {user_info[6]}\n'
                                           f'referall - {user_info[7]}\n'
                                           f'Время регистрации - {user_info[8]}\n',
                                           reply_markup=create_inline_kb(2, 'take_coins',
                                                                         'add_coins', 'give_message', last_btn='back'))
    await state.update_data(user_id=user_id)
    await state.set_state(FindUsersForDB.waiting_id_user)


# Обработка начисления фишек (Chips)
@router.callback_query(StateFilter(AddCoinsForUser.Chips_coins), F.data == 'append_accept_Chips')
async def append_accept_Chips(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    new_coins_Chips = data['new_coins_Chips']
    await db.update_coins_admin_from_user_table(user_id=str(user_id), Chips=new_coins_Chips)
    user_info = await db.show_info_by_id_for_users(user_id)
    await callback_query.message.edit_text(f'❗Информация по данному пользователю\n\n'
                                           f'id - {user_info[0]}\n'
                                           f'username - {user_info[1]}\n'
                                           f'nickname - {user_info[2]}\n'
                                           f'Lucky - {user_info[3]}\n'
                                           f'CashOnline - {user_info[4]}\n'
                                           f'OtherCoins - {user_info[5]}\n'
                                           f'Chips - {user_info[6]}\n'
                                           f'referall - {user_info[7]}\n'
                                           f'Время регистрации - {user_info[8]}\n',
                                           reply_markup=create_inline_kb(2, 'take_coins',
                                                                         'add_coins', 'give_message', last_btn='back'))
    await state.update_data(user_id=user_id)
    await state.set_state(FindUsersForDB.waiting_id_user)


# Обрабатываем 'списать монеты'
@router.callback_query(StateFilter(FindUsersForDB.waiting_id_user), F.data == 'take_coins')
async def take_coins_user(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    user_info = await db.show_info_by_id_for_users(user_id)
    await callback.message.edit_text(f'Пожалуйста, выберете монеты для списания:\n\n'
                                     f'Lucky - {user_info[3]}\n'
                                     f'CashOnline - {user_info[4]}\n'
                                     f'OtherCoins - {user_info[5]}\n'
                                     f'Chips - {user_info[6]}\n\n'
                                     f'❗Напоминаем❗\n\n'
                                     f'id клиента - {user_info[0]}\n'
                                     f'username - {user_info[1]}\n'
                                     f'nickname - {user_info[2]}\n',
                                     reply_markup=create_inline_kb(2, 'Lucky', 'CashOnline',
                                                                   'OtherCoins', 'Chips', last_btn='back_user'))
    await state.update_data(user_id=user_id)
    await state.set_state(FindUsersForDB.remove_coins_user)


# Обработка выбора монеты для списания
@router.callback_query(StateFilter(FindUsersForDB.remove_coins_user),
                       (F.data == 'Lucky') | (F.data == 'CashOnline') | (F.data == 'OtherCoins') | (F.data == 'Chips'))
async def remove_coins_user(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    user_info = await db.show_info_by_id_for_users(user_id)
    if callback.data == 'Lucky':
        await callback.message.edit_text(f'Клиент {user_info[0]}\n\n'
                                         f'Количество монет lucky - {user_info[3]}\n\n'
                                         f'Введите число монет, которое нужно будет списать.\n\n'
                                         f'❗Только целые и неполные числа❗',
                                         reply_markup=create_inline_kb(1, last_btn='back_delete'))
        await state.update_data(user_info=user_info)
        await state.set_state(RemoveCoinsForUser.lucky_coins)

    elif callback.data == 'CashOnline':
        await callback.message.edit_text(f'Клиент {user_info[0]}\n\n'
                                         f'Количество монет CashOnline - {user_info[4]}\n\n'
                                         f'Введите число монет, которое нужно будет списать.\n\n'
                                         f'❗Только целые и неполные числа❗',
                                         reply_markup=create_inline_kb(1, last_btn='back_delete'))
        await state.update_data(user_info=user_info)
        await state.set_state(RemoveCoinsForUser.CashOnline_coins)

    elif callback.data == 'OtherCoins':
        await callback.message.edit_text(f'Клиент {user_info[0]}\n\n'
                                         f'Количество монет OtherCoins - {user_info[5]}\n\n'
                                         f'Введите число монет, которое нужно будет списать.\n\n'
                                         f'❗Только целые и неполные числа❗',
                                         reply_markup=create_inline_kb(1, last_btn='back_delete'))
        await state.update_data(user_info=user_info)
        await state.set_state(RemoveCoinsForUser.OtherCoins_coins)

    elif callback.data == 'Chips':
        await callback.message.edit_text(f'Клиент {user_info[0]}\n\n'
                                         f'Количество монет Chips - {user_info[6]}\n\n'
                                         f'Введите число монет, которое нужно будет списать.\n\n'
                                         f'❗Только целые и неполные числа❗',
                                         reply_markup=create_inline_kb(1, last_btn='back_delete'))
        await state.update_data(user_info=user_info)
        await state.set_state(RemoveCoinsForUser.Chips_coins)


# Получение от пользователя числа монеты для списания
@router.message(StateFilter(RemoveCoinsForUser.lucky_coins, RemoveCoinsForUser.CashOnline_coins,
                            RemoveCoinsForUser.OtherCoins_coins, RemoveCoinsForUser.Chips_coins), F.text)
async def remove_coins_for_user(message: Message, state: FSMContext):
    data = await state.get_data()
    user_info = data['user_info']
    user_id = user_info[0]
    try:
        # Работаем с lucky
        if await state.get_state() == RemoveCoinsForUser.lucky_coins:
            if user_info[3] > float(message.text):
                new_lucky_coins = user_info[3] - float(message.text)
                await state.update_data(new_lucky_coins=new_lucky_coins, user_id=user_id)
                await message.answer(f'❗Пожалуйста подтвердите операцию❗\n\n'
                                     f'После подтверждения счёт {user_id}, будет выглядеть так:\n\n'
                                     f'lucky - {new_lucky_coins}\n\n'
                                     f'Напоминаем, баланс до списания:\n\n'
                                     f'lucky - {user_info[3]}',
                                     reply_markup=create_inline_kb(1, 'remove_accept_lucky',
                                                                   last_btn='back_user'))
            else:
                new_lucky_coins = 0
                await state.update_data(new_lucky_coins=new_lucky_coins, user_id=user_id)
                await message.answer(f'❗Пожалуйста подтвердите операцию❗\n\n'
                                     f'После подтверждения счёт {user_id}, будет выглядеть так:\n\n'
                                     f'lucky - {new_lucky_coins}\n\n'
                                     f'Напоминаем, баланс до списания:\n\n'
                                     f'lucky - {user_info[3]}',
                                     reply_markup=create_inline_kb(1, 'remove_accept_lucky',
                                                                   last_btn='back_user'))

        # Работаем с CashOnline
        elif await state.get_state() == RemoveCoinsForUser.CashOnline_coins:
            if user_info[4] > float(message.text):
                new_coins_ChashOnline = user_info[4] - float(message.text)
                await state.update_data(new_coins_ChashOnline=new_coins_ChashOnline, user_id=user_id)
                await message.answer(f'❗Пожалуйста подтвердите операцию❗\n\n'
                                     f'После подтверждения счёт {user_id}, будет выглядеть так:\n\n'
                                     f'CashOnline - {new_coins_ChashOnline}\n\n'
                                     f'Напоминаем, баланс до списания:\n\n'
                                     f'CashOnline - {user_info[4]}',
                                     reply_markup=create_inline_kb(1, 'remove_accept_CashOline',
                                                                   last_btn='back_user'))
            else:
                new_coins_ChashOnline = 0
                await state.update_data(new_coins_ChashOnline=new_coins_ChashOnline, user_id=user_id)
                await message.answer(f'❗Пожалуйста подтвердите операцию❗\n\n'
                                     f'После подтверждения счёт {user_id}, будет выглядеть так:\n\n'
                                     f'CashOnline - {new_coins_ChashOnline}\n\n'
                                     f'Напоминаем, баланс до списания:\n\n'
                                     f'CashOnline - {user_info[3]}',
                                     reply_markup=create_inline_kb(1, 'remove_accept_CashOline',
                                                                   last_btn='back_user'))

        # Работаем с OtherCoins
        elif await state.get_state() == RemoveCoinsForUser.OtherCoins_coins:
            if user_info[5] > float(message.text):
                new_coins_OtherCoins = user_info[5] - float(message.text)
                await state.update_data(new_coins_OtherCoins=new_coins_OtherCoins, user_id=user_id)
                await message.answer(f'❗Пожалуйста подтвердите операцию❗\n\n'
                                     f'После подтверждения счёт {user_id}, будет выглядеть так:\n\n'
                                     f'OtherCoins - {new_coins_OtherCoins}\n\n'
                                     f'Напоминаем, баланс до списания:\n\n'
                                     f'OtherCoins - {user_info[5]}',
                                     reply_markup=create_inline_kb(1, 'remove_accept_OtherCoins',
                                                                   last_btn='back_user'))
            else:
                new_coins_OtherCoins = 0
                await state.update_data(new_coins_OtherCoins=new_coins_OtherCoins, user_id=user_id)
                await message.answer(f'❗Пожалуйста подтвердите операцию❗\n\n'
                                     f'После подтверждения счёт {user_id}, будет выглядеть так:\n\n'
                                     f'OtherCoins - {new_coins_OtherCoins}\n\n'
                                     f'Напоминаем, баланс до списания:\n\n'
                                     f'OtherCoins - {user_info[5]}',
                                     reply_markup=create_inline_kb(1, 'remove_accept_OtherCoins',
                                                                   last_btn='back_user'))
        # Работаем с фишками (Chips)
        elif await state.get_state() == RemoveCoinsForUser.Chips_coins:
            if user_info[6] > float(message.text):
                new_coins_Chips = user_info[6] - float(message.text)
                await state.update_data(new_coins_Chips=new_coins_Chips, user_id=user_id)
                await message.answer(f'❗Пожалуйста подтвердите операцию❗\n\n'
                                     f'После подтверждения счёт {user_id}, будет выглядеть так:\n\n'
                                     f'Chips - {new_coins_Chips}\n\n'
                                     f'Напоминаем, баланс до списания:\n\n'
                                     f'Chips - {user_info[6]}',
                                     reply_markup=create_inline_kb(1, 'remove_accept_Chips',
                                                                   last_btn='back_user'))
            else:
                new_coins_Chips = 0
                await state.update_data(new_coins_Chips=new_coins_Chips, user_id=user_id)
                await message.answer(f'❗Пожалуйста подтвердите операцию❗\n\n'
                                     f'После подтверждения счёт {user_id}, будет выглядеть так:\n\n'
                                     f'Chips - {new_coins_Chips}\n\n'
                                     f'Напоминаем, баланс до списания:\n\n'
                                     f'Chips - {user_info[6]}',
                                     reply_markup=create_inline_kb(1, 'remove_accept_Chips',
                                                                   last_btn='back_user'))
    except ValueError:
        await message.answer(f'Ошибка! Пожалуйста выберете нужную вам кнопку')


# Обработка списания Lucky
@router.callback_query(StateFilter(RemoveCoinsForUser.lucky_coins), F.data == 'remove_accept_lucky')
async def remove_accept_lucky(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    new_lucky_coins = data['new_lucky_coins']
    await db.update_coins_admin_from_user_table(user_id=str(user_id), lucky=new_lucky_coins)
    user_info = await db.show_info_by_id_for_users(user_id)
    await callback.message.edit_text(f'❗Информация по данному пользователю\n\n'
                                     f'id - {user_info[0]}\n'
                                     f'username - {user_info[1]}\n'
                                     f'nickname - {user_info[2]}\n'
                                     f'Lucky - {user_info[3]}\n'
                                     f'CashOnline - {user_info[4]}\n'
                                     f'OtherCoins - {user_info[5]}\n'
                                     f'Chips - {user_info[6]}\n'
                                     f'referall - {user_info[7]}\n'
                                     f'Время регистрации - {user_info[8]}\n',
                                     reply_markup=create_inline_kb(2, 'take_coins',
                                                                   'add_coins', 'give_message', last_btn='back'))
    await state.update_data(user_id=user_id)
    await state.set_state(FindUsersForDB.waiting_id_user)


# Обработка списания CashOnline
@router.callback_query(StateFilter(RemoveCoinsForUser.CashOnline_coins), F.data == 'remove_accept_CashOline')
async def remove_accept_CashOline(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    new_coins_ChashOnline = data['new_coins_ChashOnline']
    await db.update_coins_admin_from_user_table(user_id=str(user_id), CashOnline=new_coins_ChashOnline)
    user_info = await db.show_info_by_id_for_users(user_id)
    await callback_query.message.edit_text(f'❗Информация по данному пользователю\n\n'
                                           f'id - {user_info[0]}\n'
                                           f'username - {user_info[1]}\n'
                                           f'nickname - {user_info[2]}\n'
                                           f'Lucky - {user_info[3]}\n'
                                           f'CashOnline - {user_info[4]}\n'
                                           f'OtherCoins - {user_info[5]}\n'
                                           f'Chips - {user_info[6]}\n'
                                           f'referall - {user_info[7]}\n'
                                           f'Время регистрации - {user_info[8]}\n',
                                           reply_markup=create_inline_kb(2, 'take_coins',
                                                                         'add_coins', 'give_message', last_btn='back'))
    await state.update_data(user_id=user_id)
    await state.set_state(FindUsersForDB.waiting_id_user)


# Обработка списания OtherCoins
@router.callback_query(StateFilter(RemoveCoinsForUser.OtherCoins_coins), F.data == 'remove_accept_OtherCoins')
async def remove_accept_OtherCoin(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    new_coins_OtherCoins = data['new_coins_OtherCoins']
    await db.update_coins_admin_from_user_table(user_id=str(user_id), OtherCoins=new_coins_OtherCoins)
    user_info = await db.show_info_by_id_for_users(user_id)
    await callback_query.message.edit_text(f'❗Информация по данному пользователю\n\n'
                                           f'id - {user_info[0]}\n'
                                           f'username - {user_info[1]}\n'
                                           f'nickname - {user_info[2]}\n'
                                           f'Lucky - {user_info[3]}\n'
                                           f'CashOnline - {user_info[4]}\n'
                                           f'OtherCoins - {user_info[5]}\n'
                                           f'Chips - {user_info[6]}\n'
                                           f'referall - {user_info[7]}\n'
                                           f'Время регистрации - {user_info[8]}\n',
                                           reply_markup=create_inline_kb(2, 'take_coins',
                                                                         'add_coins', 'give_message', last_btn='back'))
    await state.update_data(user_id=user_id)
    await state.set_state(FindUsersForDB.waiting_id_user)


# Обработка списания Chips
@router.callback_query(StateFilter(RemoveCoinsForUser.Chips_coins), F.data == 'remove_accept_Chips')
async def remove_accept_Chips(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    new_coins_Chips = data['new_coins_Chips']
    await db.update_coins_admin_from_user_table(user_id=str(user_id), Chips=new_coins_Chips)
    user_info = await db.show_info_by_id_for_users(user_id)
    await callback_query.message.edit_text(f'❗Информация по данному пользователю\n\n'
                                           f'id - {user_info[0]}\n'
                                           f'username - {user_info[1]}\n'
                                           f'nickname - {user_info[2]}\n'
                                           f'Lucky - {user_info[3]}\n'
                                           f'CashOnline - {user_info[4]}\n'
                                           f'OtherCoins - {user_info[5]}\n'
                                           f'Chips - {user_info[6]}\n'
                                           f'referall - {user_info[7]}\n'
                                           f'Время регистрации - {user_info[8]}\n',
                                           reply_markup=create_inline_kb(2, 'take_coins',
                                                                         'add_coins', 'give_message', last_btn='back'))
    await state.update_data(user_id=user_id)
    await state.set_state(FindUsersForDB.waiting_id_user)


# Обрабатываем отмены во время действий с клиентом
@router.callback_query(StateFilter(RemoveCoinsForUser.lucky_coins, RemoveCoinsForUser.CashOnline_coins,
                                   RemoveCoinsForUser.OtherCoins_coins, RemoveCoinsForUser.Chips_coins,
                                   AddCoinsForUser.lucky_coins, AddCoinsForUser.CashOnline_coins,
                                   AddCoinsForUser.OtherCoins_coins, AddCoinsForUser.Chips_coins,
                                   FindUsersForDB.append_coins_user, FindUsersForDB.remove_coins_user,
                                   FindUsersForDB.message_user),
                       F.data == 'back_user')
async def back_user_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    user_info = await db.show_info_by_id_for_users(user_id)
    await state.set_state(FindUsersForDB.waiting_id_user)
    await callback.message.edit_text(f'❗Информация по данному пользователю\n\n'
                                     f'id - {user_info[0]}\n'
                                     f'username - {user_info[1]}\n'
                                     f'nickname - {user_info[2]}\n'
                                     f'Lucky - {user_info[3]}\n'
                                     f'CashOnline - {user_info[4]}\n'
                                     f'OtherCoins - {user_info[5]}\n'
                                     f'Chips - {user_info[6]}\n'
                                     f'referall - {user_info[7]}\n'
                                     f'Время регистрации - {user_info[8]}\n',
                                     reply_markup=create_inline_kb(2, 'take_coins',
                                                                   'add_coins', 'give_message', last_btn='back'))
    await state.update_data(user_id=user_id)
@router.message(Command('scan'))
async def scan_web_app(message: Message):
    if message.from_user.id not in ast.literal_eval(config.tg_bot.admin_id):
        await message.answer('У вас нет прав использовать эту команду')
    else:
        web_app_url = f"https://{config.tg_bot.ipv4}:8000/scan"
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="Cканер",
            url=web_app_url)
        )
        await message.answer("Нажмите кнопку для открытия сканера QR кодов:", reply_markup=builder.as_markup())
class QRCodeCreate(StatesGroup):
    type_qr = State()
    wait_for_count_lucky = State()
@router.callback_query(F.data == 'Сгенерировать QR', StateFilter(None))
async def type_qr(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('Выберите какой тип QR код вы хотите создать', reply_markup=create_inline_kb(2, 'Бонус'))
    await state.set_state(QRCodeCreate.type_qr)

@router.callback_query(F.data.in_(['Бонус']), QRCodeCreate.type_qr)
async def bonus_or_quiz(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'Бонус':
        await callback.message.answer('Введите количество монет, которые вы хотите раздать бонусом')
        await state.set_state(QRCodeCreate.wait_for_count_lucky)

@router.message(F.text, QRCodeCreate.wait_for_count_lucky)
async def count_coins(message: Message, state: FSMContext):
    await state.update_data(count = float(message.text))
    count = await state.get_data()
    await QRCode(message.from_user.id).qr_bonus(count['count'])
    await message.bot.send_photo(chat_id=message.from_user.id, photo=FSInputFile(f'qr_code_bonus.png'),
                                          caption='Бонусный QR код сгенерирован.')
    os.remove(f'qr_code_bonus.png')

class AddMerch(StatesGroup):
    action = State()
    name = State()
    price = State()
    image_path = State()

@router.callback_query(F.data == 'Merch_Showcase')
async def what_to_do_with_merch(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('Вы хотите добавить продукт или посмотреть витрину?', reply_markup=create_inline_kb(1, 'Добавить продукт', 'Посмотреть'))
    await state.set_state(AddMerch.action)

page = 0
@router.callback_query(F.data.in_(['Добавить продукт', 'Посмотреть']), AddMerch.action)
async def action_choosed(callback: CallbackQuery, state: FSMContext):
    global page
    if callback.data == 'Добавить продукт':
        await callback.message.answer('Введите наимнование нового товара')
        await state.set_state(AddMerch.name)
    if callback.data == 'Посмотреть':
        async with aiosqlite.connect('userdata.db') as db:
            products = await db.execute('SELECT * FROM merch')
            products = await products.fetchall()
        if products == []:
            await callback.message.answer('Список товаров пуст')
            await state.clear()
        else:
            await callback.message.bot.send_photo(chat_id=callback.from_user.id, photo=FSInputFile(products[page][3]), caption=f'<b>ID</b>: {products[page][0]}\n<b>Название</b>: {products[page][1]}\n<b>Цена</b>: {products[page][2]} <b>CashOnline</b>',
                                                  reply_markup=create_inline_kb(1, 'Следующий товар', 'Редактировать', 'Удалить'))
            await state.clear()

@router.message(F.text, AddMerch.name)
async def get_name(message: Message, state: FSMContext):
    await message.answer('Введите цену товара')
    await state.update_data(name = message.text)
    await state.set_state(AddMerch.price)

@router.message(F.text, AddMerch.price)
async def get_price(message: Message, state: FSMContext):
    await message.answer('Введите путь до изображения товара.\nPS для администратора: все фотографии находятся в папке merch. Путь указывается таким образом: <b>merch/название_фотографии.формат</b>')
    await state.update_data(price = message.text)
    await state.set_state(AddMerch.image_path)

@router.message(F.text, AddMerch.image_path)
async def image_path(message: Message, state: FSMContext):
    await state.update_data(path = message.text)
    await message.answer('Вы добавили новый товар на витрину')
    data = await state.get_data()
    async with aiosqlite.connect('userdata.db') as db:
        await db.execute('INSERT INTO merch (name, price, image_path) VALUES (?, ?, ?)',
                       (data['name'], float(data['price']), data['path']))
        await db.commit()
    await state.clear()

@router.callback_query(F.data == 'Следующий товар')
async def next_product(callback: CallbackQuery):
    global page
    page += 1
    await callback.message.delete()
    async with aiosqlite.connect('userdata.db') as db:
        products = await db.execute('SELECT * FROM merch ORDER BY id')
        products = await products.fetchall()
    try:
        await callback.message.bot.send_photo(chat_id=callback.from_user.id, photo=FSInputFile(products[page][3]),
                                          caption=f'<b>ID</b>: {page + 1}\n<b>Название</b>: {products[page][1]}\n<b>Цена</b>: {products[page][2]} <b>CashOnline</b>',
                                          reply_markup=create_inline_kb(1, 'Следующий товар', 'Редактировать',
                                                                        'Удалить'))
    except IndexError:
        page = 0
        await callback.message.bot.send_photo(chat_id=callback.from_user.id, photo=FSInputFile(products[page][3]),
                                          caption=f'<b>ID</b>: {page + 1}\n<b>Название</b>: {products[page][1]}\n<b>Цена</b>: {products[page][2]} <b>CashOnline</b>',
                                          reply_markup=create_inline_kb(1, 'Следующий товар', 'Редактировать',
                                                                        'Удалить'))

class EditProduct(StatesGroup):
    choice = State()
    name = State()
    price = State()
    path = State()
@router.callback_query(F.data == 'Редактировать')
async def edit_product(callback: CallbackQuery, state: FSMContext):
    product_number = int(callback.message.caption.split('\n')[0].split(' ')[1]) - 1
    await state.update_data(product_number = product_number)
    await callback.message.answer('Выберите что хотите отредактировать', reply_markup=create_inline_kb(1, f'Изменить название №{str(product_number + 1)}', f'Изменить цену №{str(product_number + 1)}', f'Изменить фото №{str(product_number + 1)}', 'Отменить'))
    await state.set_state(EditProduct.choice)

@router.callback_query(F.data, EditProduct.choice)
async def choice(callback: CallbackQuery, state: FSMContext):
    if callback.data.__contains__('Изменить название'):
        await callback.message.answer('Введите новое название для товара')
        await state.set_state(EditProduct.name)
    if callback.data.__contains__('Изменить цену'):
        await callback.message.answer('Введите новую цену для товара')
        await state.set_state(EditProduct.price)
    if callback.data.__contains__('Изменить фото'):
        await callback.message.answer('Введите новый путь для фотографии товара')
        await state.set_state(EditProduct.path)
    if callback.data == 'Отменить':
        await state.clear()

@router.message(F.text, StateFilter(*[EditProduct.name, EditProduct.price, EditProduct.path]))
async def editing(message: Message, state: FSMContext):
    current_state = await state.get_state()
    data = await state.get_data()
    if current_state == EditProduct.name:
        async with aiosqlite.connect('userdata.db') as db:
            products = await db.execute('SELECT * FROM merch ORDER BY id')
            products = await products.fetchall()
            choosed_product = products[int(data['product_number'])]
            await db.execute('UPDATE merch SET name = ? WHERE id = ?', (message.text, choosed_product[0]))
            await db.commit()
        await message.answer(f'Вы обновили название товара на {message.text}')
    if current_state == EditProduct.price:
        async with aiosqlite.connect('userdata.db') as db:
            products = await db.execute('SELECT * FROM merch ORDER BY id')
            products = await products.fetchall()
            choosed_product = products[int(data['product_number'])]
            await db.execute('UPDATE merch SET price = ? WHERE id = ?', (message.text, choosed_product[0]))
            await db.commit()
        await message.answer(f'Вы обновили цену товара на {message.text}')
    if current_state == EditProduct.path:
        async with aiosqlite.connect('userdata.db') as db:
            products = await db.execute('SELECT * FROM merch ORDER BY id')
            products = await products.fetchall()
            choosed_product = products[int(data['product_number'])]
            await db.execute('UPDATE merch SET patg = ? WHERE id = ?', (message.text, choosed_product[0]))
            await db.commit()
        await message.answer(f'Вы обновили цену товара на {message.text}')

@router.callback_query(F.data == 'Удалить')
async def delete_product(callback: CallbackQuery):
    product_number = int(callback.message.caption.split('\n')[0].split(' ')[1]) - 1
    async with aiosqlite.connect('userdata.db') as db:
        products = await db.execute('SELECT * FROM merch ORDER BY id')
        products = await products.fetchall()
        choosed_product = products[product_number]
        await db.execute('DELETE FROM merch WHERE id = ?', (choosed_product[0],))
        await db.commit()
    await callback.message.delete()
    await callback.message.answer(f'Вы удалили товар с id {product_number + 1}')

class CreateTask(StatesGroup):
    channel = State()
    bonus = State()
@router.callback_query(F.data == 'Создать задание', StateFilter(None))
async def create_task(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('Введите ссылку на канал')
    await state.set_state(CreateTask.channel)

@router.message(F.text, CreateTask.channel)
async def het_channel(message: Message, state: FSMContext):
    await state.update_data(url = message.text)
    await message.answer('Введите вознаграждение')
    await state.set_state(CreateTask.bonus)


@router.message(F.text, CreateTask.bonus)
async def send_task(message: Message, state: FSMContext):
    await state.update_data(bonus = message.text)
    data = await state.get_data()
    async with aiosqlite.connect('userdata.db') as conn:
        ids = await conn.execute('SELECT user_id FROM users')
        ids = await ids.fetchall()
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='Проверить'), InlineKeyboardButton(text = 'Не хочу'))
    for i in ids:
        await message.bot.send_message(chat_id = int(i[0]), text=f'Подпишитесь на канал и получите бонус {data["bonus"]} LuckyCoins\n'
                                                                 f'{data["url"]}',
                                       reply_markup=builder.as_markup())
    await state.clear()


class IntervalMessage(StatesGroup):
    message = State()
    interval = State()

@router.callback_query(F.data == 'Отложенное сообщение', StateFilter(None))
async def interval_message(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('Введите текст сообщения')
    await state.set_state(IntervalMessage.message)

@router.message(F.text, IntervalMessage.message)
async def ask_interval(message: Message, state: FSMContext):
    await state.update_data(message = message.text)
    await message.answer('Введите интервал в минутах, через который вы хотите, чтоб сообщение отправилось')
    await state.set_state(IntervalMessage.interval)


async def message_interval(message, interval, bot):
    await asyncio.sleep(interval)
    async with aiosqlite.connect('userdata.db') as conn:
        ids = await conn.execute('SELECT user_id FROM users')
        ids = await ids.fetchall()
    for i in ids:
        await bot.send_message(chat_id=int(i[0]), text=message)

# В вашем обработчике сообщений:
@router.message(F.text, IntervalMessage.interval)
async def get_interval(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(interval=message.text)
    data = await state.get_data()
    interval_message_text = data['message']

    try:
        interval = float(data['interval'])  # Преобразование строки в число здесь
        task = asyncio.create_task(message_interval(interval_message_text, interval*60, bot))
        # Перевод минут в секунды для функции asyncio.sleep
        await message.answer(f'Отправка запланирована через {interval} минут(ы)')
    except ValueError:
        await message.answer('Введено неверное значение. Повторите процедуру снова.')
    await state.clear()


@router.callback_query(F.data == 'Посмотреть рефералов')
async def get_referers(callback: CallbackQuery):
    referer_referal = {}
    async with aiosqlite.connect('userdata.db') as conn:
        all_ids = await conn.execute('SELECT user_id FROM users')
        all_ids = await all_ids.fetchall()
        for i in all_ids:
            referals = await conn.execute('SELECT user_id FROM users WHERE referral = ?', (i[0], ))
            referals = await referals.fetchall()
            referals = [str(i[0]) for i in referals]
            if referals != []:
                referer_referal[str(i[0])] = str(referals)
            else:
                continue
    try:
        text = ['<b>Реферер - рефералы</b>\n\n']
        for i in referer_referal.keys():
            text.append(f'{i} - {", ".join(ast.literal_eval(referer_referal[i]))}\n')
        await callback.message.answer(''.join(text))
    except Exception:
        await callback.message.answer('Рефереров пока что нет.')


