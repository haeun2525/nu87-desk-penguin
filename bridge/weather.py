"""날씨 화면 (128×64) — Open-Meteo (키 필요 없음). 기본 위치 서울"""
import json, math, urllib.request
from PIL import Image, ImageDraw, ImageFont

LAT, LON, PLACE = 37.5665, 126.9780, "서울"   # 내 동네 위도·경도로 바꾸기
F = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
BIG = ImageFont.truetype(F, 26, index=6)
MID = ImageFont.truetype(F, 13, index=6)
SMALL = ImageFont.truetype(F, 12, index=4)


def fetch():
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
           "&current=temperature_2m,weather_code&daily=temperature_2m_max,temperature_2m_min&hourly=precipitation_probability"
           "&timezone=Asia%2FSeoul&forecast_days=1")
    j = json.load(urllib.request.urlopen(url, timeout=10))
    now_h = j["current"]["time"][:13]                    # 비 확률은 지금부터 오늘 끝까지만 (이미 지난 새벽 비는 빼기)
    pops = [p for t, p in zip(j["hourly"]["time"], j["hourly"]["precipitation_probability"]) if t[:13] >= now_h and p is not None]
    return dict(t=j["current"]["temperature_2m"], code=j["current"]["weather_code"],
                hi=j["daily"]["temperature_2m_max"][0], lo=j["daily"]["temperature_2m_min"][0],
                pop=max(pops) if pops else 0)


def kind(code):
    if code == 0: return "sun", "맑음"
    if code in (1, 2): return "partly", "구름 조금"
    if code == 3: return "cloud", "흐림"
    if code in (45, 48): return "cloud", "안개"
    if 71 <= code <= 77 or code in (85, 86): return "snow", "눈"
    if code >= 95: return "rain", "뇌우"
    if 51 <= code <= 82: return "rain", "비"
    return "cloud", "흐림"


def icon(d, k, x, y):   # 40×40 칸
    def cloud(cx, cy, s=1.0, fill=1):
        for (dx, dy, r) in ((-8, 3, 8), (2, -3, 10), (11, 4, 7)):
            d.ellipse([cx + dx * s - r * s, cy + dy * s - r * s, cx + dx * s + r * s, cy + dy * s + r * s], fill=fill)
        d.rectangle([cx - 8 * s, cy + 3 * s, cx + 11 * s, cy + 11 * s], fill=fill)
    if k in ("sun", "partly"):
        cx, cy = (x + 20, y + 20) if k == "sun" else (x + 14, y + 13)
        d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=1)
        for i in range(8):
            a = i * math.pi / 4
            d.line([cx + 12 * math.cos(a), cy + 12 * math.sin(a), cx + 17 * math.cos(a), cy + 17 * math.sin(a)], fill=1, width=2)
        if k == "partly":
            cloud(x + 23, y + 24, 0.9, 0); cloud(x + 23, y + 24, 0.75, 1)
    else:
        cloud(x + 20, y + 15)
        if k == "rain":
            for dx in (-8, 0, 8): d.line([x + 20 + dx, y + 30, x + 17 + dx, y + 37], fill=1, width=2)
        if k == "snow":
            for dx in (-8, 0, 8): d.ellipse([x + 18 + dx, y + 31, x + 22 + dx, y + 35], fill=1)


def render(w=None):
    w = w or fetch()
    k, label = kind(w["code"])
    img = Image.new("1", (128, 64)); d = ImageDraw.Draw(img)
    icon(d, k, 2, 4)
    d.text((48, 2), f"{round(w['t'])}°", font=BIG, fill=1)
    d.text((48, 32), f"{PLACE} {label}", font=MID, fill=1)
    d.text((2, 50), f"최고{round(w['hi'])}° 최저{round(w['lo'])}° 비{w['pop']}%", font=SMALL, fill=1)
    return img, w, label


def to_bytes(img):
    out = bytearray()
    for y in range(64):
        for bx in range(16):
            b = 0
            for k in range(8):
                if img.getpixel((bx * 8 + k, y)): b |= 0x80 >> k
            out.append(b)
    return bytes(out)


if __name__ == "__main__":
    img, w, label = render()
    print(w, label)
    img.convert("L").point(lambda v: 255 if v else 0).resize((512, 256), Image.NEAREST).save(__file__.rsplit("/", 1)[0] + "/weather_preview.png")
