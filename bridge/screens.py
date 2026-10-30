"""정보 화면 (128×64, 1비트) — 왼쪽 아이콘 + 오른쪽 한글 2~3줄. 보드는 'p' + 1024바이트로 받아 8초 보여줌"""
from textfix import clean
from PIL import Image, ImageDraw, ImageFont

F = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
TITLE = ImageFont.truetype(F, 14, index=6)
BODY = ImageFont.truetype(F, 12, index=4)
TX = 38            # 글자 시작 x (왼쪽 36px 은 아이콘)
TW = 128 - TX      # 글자 칸 너비


def _wrap(d, text, font, width, max_lines):
    """띄어쓰기 기준으로 줄바꿈, 한 단어가 너무 길면 글자 단위로 자름. 넘치면 마지막 줄 끝을 …"""
    fits = lambda t: d.textlength(t, font=font) <= width
    lines, cur = [], ""
    for word in text.split():
        cand = (cur + " " + word).strip()
        if fits(cand):
            cur = cand; continue
        if cur: lines.append(cur)
        cur = ""
        for ch in word:                     # 단어 하나가 한 줄보다 길 때
            if fits(cur + ch): cur += ch
            else: lines.append(cur); cur = ch
    if cur: lines.append(cur)
    if len(lines) > max_lines:
        last = lines[max_lines - 1]
        while last and not fits(last + "…"): last = last[:-1]
        lines = lines[:max_lines - 1] + [last + "…"]
    return lines


def icon(d, kind, x=2, y=14):
    """34×34 칸 아이콘"""
    if kind == "music":
        d.ellipse([x + 4, y + 22, x + 14, y + 30], fill=1); d.ellipse([x + 20, y + 18, x + 30, y + 26], fill=1)
        d.rectangle([x + 12, y + 4, x + 14, y + 26], fill=1); d.rectangle([x + 28, y, x + 30, y + 22], fill=1)
        d.polygon([(x + 12, y + 4), (x + 30, y), (x + 30, y + 6), (x + 12, y + 10)], fill=1)
    elif kind == "calendar":
        d.rectangle([x + 2, y + 4, x + 32, y + 32], outline=1, width=2); d.rectangle([x + 2, y + 4, x + 32, y + 11], fill=1)
        for cx in (x + 9, x + 25): d.rectangle([cx - 1, y, cx + 1, y + 6], fill=1)
        for r in range(2):
            for c in range(3): d.rectangle([x + 7 + c * 8, y + 16 + r * 7, x + 10 + c * 8, y + 19 + r * 7], fill=1)
    elif kind == "stretch":   # 만세 하는 사람
        d.ellipse([x + 12, y, x + 22, y + 10], fill=1)
        d.line([x + 17, y + 10, x + 17, y + 24], fill=1, width=3)
        d.line([x + 17, y + 13, x + 5, y + 2], fill=1, width=3); d.line([x + 17, y + 13, x + 29, y + 2], fill=1, width=3)
        d.line([x + 17, y + 24, x + 9, y + 34], fill=1, width=3); d.line([x + 17, y + 24, x + 25, y + 34], fill=1, width=3)
    elif kind == "check":
        d.ellipse([x + 1, y + 1, x + 33, y + 33], fill=1)
        d.line([x + 9, y + 17, x + 15, y + 24, x + 26, y + 10], fill=0, width=4)
    elif kind == "umbrella":
        d.pieslice([x + 1, y + 2, x + 33, y + 30], 180, 360, fill=1)
        d.rectangle([x + 16, y + 15, x + 18, y + 30], fill=1)
        d.arc([x + 10, y + 26, x + 18, y + 34], 0, 180, fill=1, width=2)
        for dx in (3, 30): d.line([x + dx, y + 22, x + dx - 2, y + 27], fill=1, width=1)


def screen(kind, title, body="", body_lines=2, title_lines=1):
    title, body = clean(title), clean(body)
    img = Image.new("1", (128, 64)); d = ImageDraw.Draw(img)
    icon(d, kind)
    t_lines = _wrap(d, title, TITLE, TW, 2 if not body else title_lines)
    b_lines = _wrap(d, body, BODY, TW, body_lines) if body else []
    h = len(t_lines) * 17 + len(b_lines) * 15
    y = max(0, (64 - h) // 2)
    for ln in t_lines:
        d.text((TX, y), ln, font=TITLE, fill=1); y += 17
    for ln in b_lines:
        d.text((TX, y), ln, font=BODY, fill=1); y += 15
    return img


def to_bytes(img):
    out = bytearray()
    for y in range(64):
        for bx in range(16):
            b = 0
            for k in range(8):
                if img.getpixel((bx * 8 + k, y)): b |= 0x80 >> k
            out.append(b)
    return bytes(out)


def preview(img, path):
    img.convert("L").point(lambda v: 255 if v else 0).resize((512, 256), Image.NEAREST).save(path)


# ─────────────── 메시지 내용 화면 (알림 애니메이션 뒤에 이어서) ───────────────
SMALL = ImageFont.truetype(F, 11, index=4)
TALK = ["..#######..", ".#########.", "###########", "###########", "###########",
        ".#########.", "..#######..", "..##.......", ".#........."]
MAIL = ["###########", "##.......##", "#.#.....#.#", "#..#...#..#", "#...#.#...#",
        "#....#....#", "#.........#", "###########"]


def _pix(d, rows, x, y):
    for j, row in enumerate(rows):
        for i, c in enumerate(row):
            if c == "#": d.point((x + i, y + j), 1)


def message_pages(kind, header, body, header_font=None, max_pages=2):
    """kind 'k' (카톡: header=보낸 사람, body=메시지) / 'g' (메일: header=메일 주소, body=제목)
    맨 위 줄 = 작은 아이콘 + header, 아래 3줄 = body. 길면 페이지를 나눔 (마지막 페이지 끝은 …)"""
    header, body = clean(header), clean(body)
    hf = header_font or (SMALL if kind == "g" else TITLE)
    probe = ImageDraw.Draw(Image.new("1", (1, 1)))
    head = _wrap(probe, header, hf, 128 - 15, 1)[0] if header else ""
    lines = _wrap(probe, body or "(내용 없음)", BODY, 126, 3 * max_pages)
    pages = []
    for p in range(0, len(lines), 3):
        img = Image.new("1", (128, 64)); d = ImageDraw.Draw(img)
        _pix(d, TALK if kind == "k" else MAIL, 0, 3)
        d.text((14, 0 if hf is TITLE else 2), head, font=hf, fill=1)
        d.line([0, 16, 127, 16], fill=1)
        for i, ln in enumerate(lines[p:p + 3]):
            d.text((1, 18 + i * 15), ln, font=BODY, fill=1)
        if p + 3 < len(lines):                     # 다음 페이지 있음 표시 ▼
            d.polygon([(122, 59), (127, 59), (124, 63)], fill=1)
        pages.append(img)
    return pages
