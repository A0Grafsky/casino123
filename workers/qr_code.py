import random

import qrcode
from config_data.config import Config, load_config

config: Config = load_config()

class QRCode():
    def __init__(self, user_id):
        self.user_id = user_id

    async def code_generate(self):
        url = f"https://{config.tg_bot.ipv4}:8000/transactions?user_id={self.user_id}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        img.save(f"qr_code_{self.user_id}.png")

    async def qr_bonus(self, count):
        url = f"https://{config.tg_bot.ipv4}:8000/bonus?count={count}&token={random.randint(10000, 99999)}"
        print(url)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        img.save(f"qr_code_bonus.png")