"""이름 글자를 OLED 용 1비트 그림(128×16, 256바이트)으로. 한글은 보드 글꼴에 없어서 맥에서 그려 보냄."""
from textfix import clean
from PIL import Image, ImageDraw, ImageFont

W, H = 128, 16
FONT = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 14, index=6)   # 6 = Bold 계열


def render(text):
    text = clean(text)
    img = Image.new("1", (W, H), 0)
    d = ImageDraw.Draw(img)
    text = " ".join(text.split())
    while text and d.textlength(text, font=FONT) > W:      # 넘치면 뒤를 자르고 …
        text = text[:-2] + "…"
    x = max(0, (W - d.textlength(text, font=FONT)) // 2)
    d.text((x, H // 2 + 2), text, font=FONT, fill=1, anchor="lm")
    return img


def to_bytes(img):
    """한 줄 = 16바이트, 왼쪽 픽셀이 MSB"""
    out = bytearray()
    for y in range(H):
        for bx in range(W // 8):
            b = 0
            for k in range(8):
                if img.getpixel((bx * 8 + k, y)):
                    b |= 0x80 >> k
            out.append(b)
    return bytes(out)


if __name__ == "__main__":
    import sys
    img = render(sys.argv[1] if len(sys.argv) > 1 else "김누누")
    for y in range(H):
        print("".join("#" if img.getpixel((x, y)) else "." for x in range(W)))


def text_width(text):
    text = clean(text)
    d = ImageDraw.Draw(Image.new("1", (1, 1)))
    return int(d.textlength(" ".join(text.split()), font=FONT))


def render_wide(text, w=256):
    text = clean(text)
    """긴 이름(메일 주소 등) — 256×16 에 왼쪽 정렬. 보드가 옆으로 흘려 보여줌"""
    img = Image.new("1", (w, H), 0)
    d = ImageDraw.Draw(img)
    text = " ".join(text.split())
    while text and d.textlength(text, font=FONT) > w - 4:
        text = text[:-2] + "…"
    d.text((2, H // 2 + 2), text, font=FONT, fill=1, anchor="lm")
    return img, min(w, int(d.textlength(text, font=FONT)) + 4)


def to_bytes_w(img):
    out = bytearray()
    W2 = img.size[0]
    for y in range(H):
        for bx in range(W2 // 8):
            b = 0
            for k in range(8):
                if img.getpixel((bx * 8 + k, y)): b |= 0x80 >> k
            out.append(b)
    return bytes(out)
