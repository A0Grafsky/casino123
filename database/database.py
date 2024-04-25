import aiosqlite


# Создание БД rate_coins (курс обмена)
async def create_rate_coins():
    async with aiosqlite.connect('userdata.db') as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS rate_coins (id INTEGER PRIMARY KEY,"
            "from_currency TEXT, to_currency TEXT, rate REAL)"
        )
        await db.commit()


# Создание БД admin (админ)
async def create_admin():
    async with aiosqlite.connect('userdata.db') as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS admins (admin_id INTEGER PRIMARY KEY,"
            "username TEXT, Lucky REAL, CashOnline REAL, OtherCoins Real)"
        )
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


# Создание БД users (пользователи)
async def create_users():
    async with aiosqlite.connect('userdata.db') as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, "
            "username TEXT, nickname TEXT, Lucky REAL, CashOnline REAL, OtherCoins Real, "
            "referral TEXT, current_time TIMESTAMP)"
        )
        await db.commit()


# Вытаскиваем user_id из БД users
async def user_id_from_users():
    async with aiosqlite.connect('userdata.db') as con:
        cursor = await con.execute(F'SELECT user_id FROM users')
        row = await cursor.fetchall()
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
        cursor = await con.execute(F'SELECT nickname FROM users WHERE user_id = ?', (user_id, ))
        row = await cursor.fetchall()
    return row


# Вытаскиваем монеты из БД user
async def coins_user_from_users(user_id: str):
    async with aiosqlite.connect('userdata.db') as con:
        cursor = await con.execute(f'SELECT Lucky, CashOnline, OtherCoins FROM users WHERE user_id= ?', (user_id, ))
        row = await cursor.fetchall()
    return row


# Добавляем данные в БД users
async def add_user_to_users_table(user_id: str, username: str, nickname, Lucky: float, CashOnline: float,
                                  OtherCoins: float, current_time):
    async with aiosqlite.connect('userdata.db') as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, nickname, Lucky, CashOnline, OtherCoins, current_time)"
            "VALUES (?, ?, ?, ?, ?, ?, ?)", (user_id, username, nickname, Lucky, CashOnline, OtherCoins, current_time)
        )
        await db.commit()