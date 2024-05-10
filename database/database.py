import os

import aiosqlite
import json
import pprint


# Создание БД для квизов
async def crete_quizzes():
    async with aiosqlite.connect('userdata.db') as db:
        await db.execute(
            'CREATE TABLE IF NOT EXISTS quizzes (id_quizzes INTEGER PRIMARY KEY,'
            'name_quiz TEXT, one_question TEXT, one_answer TEXT, two_question TEXT, two_answer TEXT,'
            'three_question TEXT, three_answer TEXT, prize TEXT)'
        )
        await db.commit()

# Добавление в БД новых квизов
async def append_new_quizzes(name_quizzes, one_question, one_answer, two_question, two_answer,
                             three_question, three_answer, prize):
    async with aiosqlite.connect('userdata.db') as db:
        await db.execute(
            'INSERT OR IGNORE INTO quizzes (name_quiz, one_question, one_answer, two_question,'
            'two_answer, three_question, three_answer, prize)'
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (name_quizzes, one_question, one_answer,
                                                two_question, two_answer, three_question, three_answer, prize)
        )
        await db.commit()

async def create_task_table():
    async with aiosqlite.connect('userdata.db') as db:
        await db.execute('CREATE TABLE IF NOT EXISTS task (id INTEGER PRIMARY KEY, url TEXT, bonus TEXT)')
        await db.commit()
# Запись БД в json-файл
async def info_quizzes_for_quizzes_json():
    async with aiosqlite.connect('userdata.db') as con:
        cursor = await con.execute(f'SELECT * FROM quizzes')
        data = await cursor.fetchall()
    exchange_data_quizzes = []
    for row in data:
        exchange_data_quizzes.append({str(row[1]): {str(row[2]): str(row[3]), str(row[4]): str(row[5]), str(row[6]): str(row[7]), "награда": str(row[8])}})
    with open('exchange_look_quizzes.json', 'w', encoding='utf-8') as json_file:
        json.dump(exchange_data_quizzes, json_file, ensure_ascii=False, indent=4)

# Создание БД для отложенных сообщений
async def create_old_message():
    async with aiosqlite.connect('userdata.db') as db:
        await db.execute(
            'CREATE TABLE IF NOT EXISTS old_message (id INTEGER PRIMARY KEY, '
            'name_old_message TEXT, text_old_message TEXT)'
        )
        await db.commit()


# Вытаскиваем все отложенные сообщения из бд old_message
async def info_from_old_message():
    async with aiosqlite.connect('userdata.db') as con:
        cursor = await con.execute(f'SELECT * FROM old_message')
        rows = await cursor.fetchall()
    return rows


# Вытаскиваем отложенные сообщения из бд по названию
async def info_old_message_for_name(name):
    async with aiosqlite.connect('userdata.db') as con:
        cursor = await con.execute(f'SELECT text_old_message FROM old_message WHERE name_old_message = ?',
                                   (name, ))
        row = await cursor.fetchone()
    return row

# Обновляем значения отложенных сообщений
async def change_old_message(name_old_message, new_name_old_message=None, text_old_message=None):
    async with aiosqlite.connect('userdata.db') as db:
        if new_name_old_message is not None:
            await db.execute('UPDATE old_message SET name_old_message = ? WHERE name_old_message = ?',
                             (new_name_old_message, name_old_message),)
            await db.commit()

        if text_old_message is not None:
            await db.execute('UPDATE old_message SET text_old_message = ? WHERE name_old_message = ?',
                             (text_old_message, name_old_message),)
            await db.commit()


# Добавляем новое отложенное сообщение
async def append_new_old_message(name, text):
    async with aiosqlite.connect('userdata.db') as db:
        await db.execute(f'INSERT OR IGNORE INTO old_message (name_old_message, text_old_message)'
                         f'VALUES (?, ?)', (name, text))
        await db.commit()


# Удаляем отложенное сообщение
async def delete_old_message(name):
    async with aiosqlite.connect('userdata.db') as db:
        await db.execute(f'DELETE FROM old_message WHERE name_old_message = ?', (name,))
        await db.commit()


# Сохраняем все отложенные сообщения в json-файл
async def info_from_old_message_in_json():
    async with aiosqlite.connect('userdata.db') as con:
        cursor = await con.execute(f'SELECT * FROM old_message')
        data = await cursor.fetchall()
        await con.commit()
    exchange_data_old = []
    for row in data:
        exchange_data_old.append({
            row[1]: row[2]
        })
    with open('exchange_data_old.json', 'w', encoding='utf-8') as json_file:
        pprint.pprint(exchange_data_old, json_file, indent=3)


# Создание БД rate_coins (курс обмена)
async def create_rate_coins():
    async with aiosqlite.connect('userdata.db') as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS rate_coins (id INTEGER PRIMARY KEY,"
            "from_currency TEXT, to_currency TEXT, rate REAL, current_time TIMESTAMP)"
        )
        await db.commit()
        await db.execute(
            'INSERT OR IGNORE INTO rate_coins (id, from_currency, to_currency, rate)'
            'VALUES (?, ?, ?, ?)',
            (1, 'Lucky', 'CashOnline', 1.5)
        )
        await db.commit()
        await db.execute(
            'INSERT OR IGNORE INTO rate_coins (id ,from_currency, to_currency, rate)'
            'VALUES (?, ?, ?, ?)',
            (2, 'CashOline', 'Chips', 1.5)
        )
        await db.commit()


# Вытаскиваем курс из базы данных
async def if_rate_coins_for_table():
    async with aiosqlite.connect('userdata.db') as con:
        cursor = await con.execute(f"SELECT from_currency, to_currency, rate FROM rate_coins")
        row = await cursor.fetchall()
    return row


# Обновляем курс в БД rate_coins
async def change_rate_coins_for_table_rate(rate_coins, id_coins):
    async with aiosqlite.connect('userdata.db') as db:
        await db.execute(f'UPDATE rate_coins SET rate = ? WHERE id = ?', (rate_coins, id_coins,))
        await db.commit()


# Создание БД admin (админ)
async def create_admin():
    async with aiosqlite.connect('userdata.db') as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS admins (admin_id INTEGER PRIMARY KEY,"
            "username TEXT, Lucky REAL, CashOnline REAL, OtherCoins Real, Chips Real)"
        )
        await db.commit()

async def create_merch():
    async with aiosqlite.connect('userdata.db') as db:
        await db.execute('CREATE TABLE IF NOT EXISTS merch (id INTEGER PRIMARY KEY AUTOINCREMENT,'
                         'name VARCHAR(255),'
                         'price DECIMAL(10, 2),'
                         'image_path VARCHAR(255))')
        await db.commit()


# Добавление данных в БД admin
async def add_admin_to_admin_table(admin_id: str, username: str, Lucky: float, CashOnline: float,
                                   OtherCoins: float):
    async with aiosqlite.connect('userdata.db') as db:
        await db.execute(
            "INSERT OR IGNORE INTO admins (admin_id, username, Lucky, CashOnline, OtherCoins)"
            "VALUES (?, ?, ?, ?, ?)",
            (admin_id, username, Lucky, CashOnline, OtherCoins)
        )
        await db.commit()


# Обновляем данные таблицы после списания
async def update_coins_admin_from_user_table(user_id: str, lucky=None, CashOnline=None, OtherCoins=None, Chips=None):
    async with aiosqlite.connect('userdata.db') as db:
        if lucky is not None:
            await db.execute('UPDATE users SET Lucky = ? WHERE user_id = ?', (lucky, user_id,))
            await db.commit()
        if CashOnline is not None:
            await db.execute('UPDATE users SET CashOnline = ? WHERE user_id = ?', (CashOnline, user_id))
            await db.commit()
        if OtherCoins is not None:
            await db.execute('UPDATE users SET OtherCoins = ? WHERE user_id = ?', (OtherCoins, user_id))
            await db.commit()
        if Chips is not None:
            await db.execute('UPDATE users SET Chips = ? WHERE user_id = ?', (Chips, user_id))
            await db.commit()


# Создание БД users (пользователи)
async def create_users():
    async with aiosqlite.connect('userdata.db') as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, "
            "username TEXT, nickname TEXT, Lucky REAL, CashOnline REAL, OtherCoins Real,"
            "Chips Real, referral TEXT DEFAULT '[]', current_time TIMESTAMP)"
        )
        await db.commit()


# Вытаскиваем user_id из БД users
async def user_id_from_users():
    async with aiosqlite.connect('userdata.db') as con:
        cursor = await con.execute(F'SELECT user_id FROM users')
        row = await cursor.fetchall()
    return row


# Вытаскиваем всю инфу по id из БД users
async def show_info_by_id_for_users(user_id: str):
    async with aiosqlite.connect('userdata.db') as con:
        cursor = await con.execute(F'SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = await cursor.fetchone()
    return row


# Вытаскиваем nickname из БД users
async def nickname_from_users():
    async with aiosqlite.connect('userdata.db') as con:
        cursor = await con.execute(F'SELECT nickname FROM users')
        row = await cursor.fetchall()
    return row


# Вытаскиваем nickname по id из БД users
async def nickname_from_users_where_id(user_id: str):
    async with aiosqlite.connect('userdata.db') as con:
        cursor = await con.execute(F'SELECT nickname FROM users WHERE user_id = ?', (user_id,))
        row = await cursor.fetchall()
    return row


# Вытаскиваем монеты из БД user по id
async def coins_user_from_users(user_id: str):
    async with aiosqlite.connect('userdata.db') as con:
        cursor = await con.execute(f'SELECT Lucky, CashOnline, OtherCoins, Chips FROM users WHERE user_id= ?',
                                   (user_id,))
        row = await cursor.fetchall()
    return row


# Обновляем кошелёк пользователя из БД user после покупки
async def update_coin_for_user(user_id: str, Lucky_coin: float, CashOnline: float):
    async with aiosqlite.connect('userdata.db') as db:
        await db.execute(
            f'UPDATE users SET Lucky = ?, CashOnline = CashOnline + ? WHERE user_id = ?',
            (Lucky_coin, CashOnline, user_id,)
        )
        await db.commit()


# Добавляем данные в БД users
async def add_user_to_users_table(user_id: str, username: str, nickname, Lucky: float, CashOnline: float,
                                  OtherCoins: float, Chips: float, current_time):
    async with aiosqlite.connect('userdata.db') as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, nickname, Lucky, CashOnline, OtherCoins, Chips, current_time)"
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [user_id, username, nickname, Lucky, CashOnline, OtherCoins, Chips,  current_time]
        )
        await db.commit()


# Сохраняем базу юзеров в json-файл
async def info_user_for_user(user_id, current_time):
    async with aiosqlite.connect('userdata.db') as con:
        cursor = await con.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        data = await cursor.fetchall()
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
            "current_time": current_time
        })
    if os.path.exists('exchange_data.json') == True:
        with open('exchange_data.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        data.append(exchange_data[0])
        with open('exchange_data.json', 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
    else:
        with open('exchange_data.json', 'w', encoding='utf-8') as json_file:
            json.dump(exchange_data, json_file, ensure_ascii=False, indent=4)

async def give_bonus(count, user_id):
    async with aiosqlite.connect('userdata.db') as conn:
        count_lucky = await conn.execute('SELECT Lucky FROM users WHERE user_id = ?', (user_id,))
        count_lucky = await count_lucky.fetchall()
        await conn.execute('UPDATE users SET Lucky = ? WHERE user_id = ?', (count_lucky[0][0] + count, user_id))
        await conn.commit()