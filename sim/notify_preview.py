"""desk_pet 화면 미리보기 — 펌웨어 drawFace 를 그대로 옮겨 GIF 로 (128×64 → 4배)"""
import math, sys
from PIL import Image, ImageDraw
sys.path.insert(0, __file__.rsplit("/sim/", 1)[0] + "/bridge")
from name_bitmap import render

S = 0.66
TALK = ["..#######..", ".#########.", "###########", "###########", "###########",
        ".#########.", "..#######..", "..##.......", ".#........."]
MAIL = ["###########", "##.......##", "#.#.....#.#", "#..#...#..#", "#...#.#...#",
        "#....#....#", "#.........#", "###########"]
r = lambda v: int(round(v))


def pix(d, rows, x, y, k=1):
    for j, row in enumerate(rows):
        for i, c in enumerate(row):
            if c == "#": d.rectangle([x + i * k, y + j * k, x + i * k + k - 1, y + j * k + k - 1], fill=1)


def arc(d, cx, cy, r0, r1, a0, a1):
    for y in range(cy - r1, cy + r1 + 1):
        for x in range(cx - r1, cx + r1 + 1):
            dx, dy = x - cx, y - cy; d2 = dx * dx + dy * dy
            if d2 > r1 * r1 or d2 < r0 * r0: continue
            a = math.degrees(math.atan2(dy, dx)) % 360
            if a0 <= a <= a1: d.point((x, y), 1)


def frame(state, t, kind=None, name=None, unread=(), gx=0):
    img = Image.new("1", (128, 64)); d = ImageDraw.Draw(img)
    name_row = state == "notify" and name
    cx, cy = (48 if state == "notify" else 64), (22 if name_row else 31)
    ox = gx * 14 * S
    eyeY = r(cy - 12 * S); gap = 32 * S
    for ex in (cx - gap + ox, cx + gap + ox):
        ex = r(ex)
        if state == "notify":
            rr = r(13 * S); d.ellipse([ex - rr, eyeY - rr, ex + rr, eyeY + rr], fill=1)
            ri = r(5 * S); d.ellipse([ex - ri, eyeY - ri, ex + ri, eyeY + ri], fill=0)
        else:
            w, h = r(26 * S), r(32 * S)
            d.rounded_rectangle([ex - w // 2, eyeY - h // 2, ex + w // 2, eyeY + h // 2], radius=5, fill=1)
    my = r(cy + 26 * S - 2 * S)
    if state == "notify":
        d.ellipse([r(cx + ox) - 3, my - 3, r(cx + ox) + 3, my + 3], outline=1)
        by = (12 if name_row else 18) - r(abs(math.sin(t * 7)) * 6)
        pix(d, TALK if kind == "k" else MAIL, 98, by, 2)
        d.rectangle([122, by - 10, 124, by - 4], fill=1); d.rectangle([122, by - 1, 124, by], fill=1)
        if name_row: img.paste(render(name), (0, 48))
    else:
        a, b = r(6 * S), r(9.5 * S); arc(d, r(cx + ox), my - a, a, b, 35, 145)
        x = 116
        if "k" in unread: pix(d, TALK, x, 1); x -= 13
        if "g" in unread: pix(d, MAIL, x, 1)
    return img


def show(img):
    big = img.convert("L").point(lambda v: 255 if v else 0).resize((512, 256), Image.NEAREST)
    out = Image.new("RGB", (560, 304), (20, 20, 20))
    tint = Image.new("RGB", big.size, (120, 200, 255)); out.paste(tint, (24, 24), big)
    return out


frames = []
for i in range(30): frames.append(show(frame("idle", i / 30, gx=math.sin(i / 10) * 0.5)))
for i in range(75): frames.append(show(frame("notify", i / 15, "k", "엄마")))
for i in range(20): frames.append(show(frame("idle", i / 30, unread="k")))
for i in range(75): frames.append(show(frame("notify", i / 15, "g", "누코드 스터디")))
for i in range(30): frames.append(show(frame("idle", i / 30, unread="kg")))
outp = __file__.rsplit("/", 1)[0] + "/notify_preview.gif"
frames[0].save(outp, save_all=True, append_images=frames[1:], duration=66, loop=0)
frames[45].save(outp.replace(".gif", "_still.png"))
print(outp)
