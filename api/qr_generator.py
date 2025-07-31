import qrcode
def generate_qr(data):
    img = qrcode.make(data)
    type(img)  # qrcode.image.pil.PilImage
    img.save(f"{data['arac_id']}_{data['username']}.png")
