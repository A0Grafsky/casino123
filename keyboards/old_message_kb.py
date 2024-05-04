from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from lexicon.lexicon_ru import LEXICON_RU


# Клавиатура для показа отложенных сообщений
def get_name_keyboard(name, last_btn: str | None = None,):
    builder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []
    for i in range(len(name)):
        buttons.append(InlineKeyboardButton(text=f'Текст - {name[i]}',
                                            callback_data=f'Текст - {name[i]}'))
    builder.row(*buttons, width=1)

    if last_btn:
        builder.row(InlineKeyboardButton(
            text=LEXICON_RU[last_btn] if last_btn in LEXICON_RU else last_btn,
            callback_data=last_btn
        ))
    return builder.as_markup()


# Клавиатура для отправки отложенного сообщения
def give_old_message_keyboard(name, last_btn: str | None = None,):
    builder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []
    for i in range(len(name)):
        buttons.append(InlineKeyboardButton(text=f'Отправить {name[i]}',
                                            callback_data=f'Отправить {name[i]}'))
    builder.row(*buttons, width=1)

    if last_btn:
        builder.row(InlineKeyboardButton(
            text=LEXICON_RU[last_btn] if last_btn in LEXICON_RU else last_btn,
            callback_data=last_btn
        ))
    return builder.as_markup()
