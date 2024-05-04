import qrcode

class QRCode():
    def __init__(self, user_id):
        self.user_id = user_id

    async def code_generate(self):
        url = f"https://192.168.0.105:8000/transactions?user_id={self.user_id}"
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
        url = f"https://192.168.0.105:8000/bonus?count={count}"
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