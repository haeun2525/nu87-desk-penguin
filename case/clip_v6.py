"""
식빵 펫 — 노트북 걸이형 6차 (build123d) : 펭귄 "다리 대롱" (v5 구조 그대로)

v5 와 다른 점 (2026-10-26, 사용자 선택 — sim/penguin5.html "다리 대롱")
  - 머리: 둥근 정수리(위 모서리 R8, 높이 36), 혹 없음. 터치는 정수리 안 (OLED 바로 위)
  - 테두리 = 하트형 펭귄 얼굴 (흰색). 부리·볼 없음 (사용자: 별로)
  - 양옆 작은 날개 (머리와 한 덩어리, 앞쪽 7mm 두께)
  - 고리의 팔 → 주황 다리 + 납작한 발
  색: 머리·뒷판 검정 / 얼굴 흰색 / 다리 주황 / 뚜껑 흰색(숨음)

(아래는 v5 설명)

v4 와 다른 점 (2026-10-26, 사용자 선택 "매달린 팔 14mm" — sim/robots.html)
  - 머리: 35 × 33 TV 로봇 (OLED 가 허락하는 거의 최소) + 위에 혹(점 하나). 털·귀 없음
  - 터치(TTP223)는 머리 위 **혹 안**에 눕힘 → 혹 = 터치 버튼
  - 고리 = 안장 + **팔 두 개**(덮개 앞에 14mm 매달림). 팔이 앞 립 역할
  - 핀 대신 **필라멘트 조각(1.75mm)을 다월**로 — 머리·고리 둘 다 구멍만 있다

(아래는 v4 설명)

v3 와 다른 점
  - 덮개 위로 보이는 건 **OLED + 테두리만 담은 작은 머리**(약 32 × 37mm).
  - NU87 Tiny DK 는 덮개 **뒤** 주머니에 세로로 세운다. 안테나 끝(위)이 덮개 윗모서리 위로
    올라와 알루미늄에서 벗어나고, USB-C 는 아래를 향해 노트북 USB 로 바로 꽂는다.
  - 보드에 충전 회로가 없어서 **기본은 배터리 없음**(BATTERY=False). 노트북 USB 로 동작.
    True 로 하면 덮개와 DK 사이에 작은 LiPo + TP4056 칸을 넣는다 (아래 build(True)).

    옆에서 본 단면 (왼쪽 = 뒤, 오른쪽 = 앞/사용자 쪽)

                 ┌─────┐ ← 머리: OLED + 하늘색 테두리, 정수리 안쪽에 터치
           ┌──┐  │OLED │
           │DK│▐▌│     │   (DK 안테나 끝이 덮개 위로 올라옴)
           │  │▐▌└──┬──┘
           │  │▐▌덮개│▌ ← 앞 립(베젤만)
           │  │▐▌    │
           └▽─┘▐▌    │ ← 노트북 화면
            USB-C ↓ 케이블은 노트북 뒤로

부품 (4개, 2색)
  head   흰색   머리 껍데기 — 뒤가 열린 앞판+옆벽. 걸이의 뒷판에 붙어서 닫힌다
  bezel  흰 하트 얼굴 — 평평한 머리 앞면에 핀 2개로 자리 잡고 접착
  hook   흰색   걸이 — 안장 + 앞 립 + 머리 뒷판 + DK 주머니(덮개 뒤)
  cover  흰색   주머니 뚜껑 — RESET·PA27·BOOT 버튼 구멍 + RGB LED 창

좌표:   x = 폭, y = 높이(0 = 덮개 윗모서리), z = 앞뒤(0 = 덮개 앞면, +사용자 쪽)
보드 방향: 부품 면(버튼·USB-C)이 **뒤(-z)** 를 향한다 → 뚜껑 구멍으로 버튼을 누른다.
출력:   head 는 앞면이 베드, hook 은 옆으로 눕힘(주머니 옆벽이 6~12mm 다리 — 서포트 없이 됨),
        bezel·cover 는 납작하게. out/clip6_*_print.stl
실행:   ~/cad/.venv/bin/python clip_v6.py   → out/clip6_* (배터리 없음), out/clip6b_* (배터리 있음)

⚠️ ❓ 표시는 실측 전 가안 — 캘리퍼로 재면 상수만 바꿔 다시 뽑는다.
"""
import json
from pathlib import Path
from build123d import *

BATTERY = False      # 기본: 배터리 없음 (보드에 충전 회로가 없다). 아래에서 두 경우 다 뽑아 무게를 비교한다

# ─────────────── 노트북 ───────────────
LID_T = 4.0          # 맥북 에어 M2 덮개 두께 — 공식 값 없음(닫힌 두께 11.3 중 덮개 ≈ 4). 고리를 틈 3종으로 뽑는다
PAD = 0.4            # 안쪽 미끄럼방지 패드 자리
LIP_D = 4.0          # 앞 립 (베젤만)

# ─────────────── 부품 ───────────────
DK = (25.37, 41.30)  # ✅ NU87 Tiny DK (사용자 실측, 세로로 세움: x 폭, y 높이)
DK_T = 7.0           # ✅ 사용자: 깊이는 늘린 것(7.4) 유지. USB-C 가 판에서 약 5mm, 부품만은 약 2mm
DK_PCB = 1.0         # ❓ PCB 두께
USB_OUT = 0.5        # ✅ USB-C 는 PCB 끝과 거의 같은 높이 (사용자: 1mm 안 됨)
# 부품 면에서 본 위치 (bx = 왼쪽 끝에서, by = 위(안테나) 끝에서, mm) — 사진 비율로 추정 ❓
BTN = {"PA27": (5.1, 21.7), "BOOT": (20.4, 21.8), "RESET": (20.6, 38.1)}
LED = (20.4, 30.0)
ANT_LEN = 5.0        # 안테나가 차지하는 위쪽 끝 길이 (모듈 맨 위)

OLED_PCB = (24.7, 27.0, 1.2)   # ✅ 기판 실크 "24.7x27x1.2" (사용자 사진 IMG_5008)
OLED_GLASS = (26.7, 19.3, 1.6) # ❓ 유리
OLED_WIN = (23.0, 12.0)        # 보이는 창
GLASS_DY = -1.0      # ❓ 유리 중심이 PCB 중심보다 아래로 (4핀이 위쪽 끝)
TOUCH = (15.0, 11.0, 2.2)      # ❓ TTP223 (x, z, 두께) — 패드 면이 정수리 안쪽 벽에
LIPO = (20.0, 30.0, 5.0)       # ❓ 배터리 모드용 502030 (250mAh 급)
TP4056 = (27.0, 17.0, 4.0)     # ❓ 충전 모듈 (가로로 눕힘, 충전 단자는 +x 옆)
FIT = 0.4

# ─────────────── 머리 ───────────────
SIDE = 1.4
FRONT = 1.6
FLOOR = 1.2
TOP_THIN = 1.2
SAD = 2.0                                  # 안장 두께
HEAD_W = 35.0                              # 로봇 머리 폭 — OLED 27.3 + 벽. 42 는 너무 크다(사용자) → 최소 근처로
CAV_HW = HEAD_W / 2 - SIDE                 # 속 반폭 14.6
OLED_Y0 = SAD + FLOOR + FIT                # OLED PCB 아래 끝
OLED_Y1 = OLED_Y0 + OLED_PCB[1]
TOUCH_ON = bool(int(__import__("os").environ.get("TOUCH", "0")))                          # ✅ 사용자: 이번 버전은 터치센서 없음 → OLED 위 빈칸 없앰
CAV_TOP = OLED_Y1 + FIT + ((TOUCH[2] + 0.3) if TOUCH_ON else 0.0)   # 속 천장
FACE_UP = 2.0                              # ✅ 사용자: 디스플레이 아래가 보임 → 하트 얼굴(홈+창)을 통째로 2mm 위로. 흰 얼굴판은 그대로 쓰고 자리만 올라감
HEAD_TOP = 36.0 if TOUCH_ON else CAV_TOP + 1.6 + FACE_UP   # 둥근 정수리 (터치 없으면 OLED 바로 위 + 벽 1.6)
R_TOP, R_BOT = (8.0 if TOUCH_ON else 7.0), 4.0   # 펭귄 머리: 위를 둥글게 (낮아진 머리는 7 — 모서리 벽 두께 유지)
FLIP = (18.6, 15.0, 2.4, 6.5, 14.0, 7.0)   # 날개 (중심 x, y, 반폭, 반높이, 기울기°, 앞쪽 두께)
MASK = dict(ex=6.6, ey=21.5 + FACE_UP, rx=9.0, ry=8.6, hw=14.6, y0=6.2 + FACE_UP, y1=21.0 + FACE_UP, rb=5.0)   # 하트 얼굴 (sim/penguin5.html)
FOOT = (4.2, 2.2)                          # 발 타원 반지름 (가로, 세로)
ARM_L = 14.0                               # ✅ 팔: 덮개 윗모서리에서 손끝까지 (사용자 선택)
ARM_X = (10.5, 15.0)                       # 팔 x 범위 (가운데에서)
ARM_T = 2.2                                # 팔 두께 (앞뒤)
DOWEL_R = 0.95                             # 필라멘트 1.75 다월 구멍
HEAD_D0 = 13.0                             # 처음 머리 깊이 — 고리(주황)·다월은 이 기준 그대로 (다시 안 뽑게)
HEAD_D = float(__import__("os").environ.get("HEAD_D", 13.0))   # ✅ 사용자: 핀헤더에 점퍼선(듀폰 14mm) 꽂을 틈 → 13→24, OLED 뒤 약 19.6mm
Z_FI = -(LID_T + PAD)                      # 걸이 뒷판 앞면 = 머리 뒷면
Z_F = Z_FI + HEAD_D                        # 머리 앞면
Z_F0 = Z_FI + HEAD_D0
HOLE_Y = (OLED_Y1 - 5.0, CAV_TOP)          # ✅ 사용자: 점퍼 꽂은 높이와 구멍이 안 맞음 → 핀헤더(OLED 윗변 ~1.5 아래) 높이로. 예전 16.5~22.5
GLASS_CY = OLED_Y0 + 27.8 / 2 + GLASS_DY   # 창 위치는 사용자가 실물로 맞춘 값 그대로 (옛 가정치 27.8 기준)
WIN_DY = 1.0         # ✅ 1판 테스트: 창 아래로 OLED 부품이 보임 → 창만 1mm 위로 (OLED 자리는 그대로)
WIN_CY = GLASS_CY + WIN_DY + FACE_UP
WIN_TOP_ADD = 1.0    # ✅ 창 위쪽 끝만 1mm 더 (창 높이 12 → 13)
FACE_GROW_X, FACE_GROW_TOP = 0.0, 0.0   # 얼굴판·홈은 원래 크기 (잘못 키웠던 것 되돌림)

BZ_W, BZ_H, BZ_R = 29.0, 18.0, 4.0
BZ_T, BZ_IN, BZ_CLR = 1.8, 1.2, 0.1   # ✅ 사용자: 틈 0.3 은 접착 자리가 없음 → 머리 홈을 줄여 0.1 끼움 (얼굴판은 이미 뽑은 그대로)
BZ_LEDGE = 0.5   # ✅ 홈 바닥은 가운데를 뚫고 가장자리 턱(얼굴판 밑 0.5, 두께 0.4)만 — 통짜 바닥은 허공 브리지라 실뭉치 (IMG_5009)
BZ_PINS = []  # (핀 쓰려면 [(-11.0, 8.0), (11.0, 8.0)]) 사용자가 이미 핀 없는 1.8 얼굴판을 뽑아서 없음. 창 맞춰 붙임. 얼굴판 뒤 자리 핀 (⌀1.4, 길이 0.8) ↔ 머리 앞면 구멍 (⌀1.8, 깊이 1.0)

# ─────────────── 걸이 + 주머니 ───────────────
WALL = 1.2
Z_FO = Z_FI - WALL                         # 뒷판 뒷면 (= 주머니 앞벽 뒷면)
Y_TOP = 12.0                               # DK 위 끝 높이 — 안테나(위 5mm)가 덮개(0)보다 7mm 이상 위
PK_HW0 = DK[0] / 2 + 0.3 + 1.0             # 주머니 속 반폭 (✅ 테스트: 양쪽 1mm씩 더. 오른쪽은 WIDEN_R 1mm 가 또 더해짐)
USB_W = (-7.8, 6.8)                        # USB-C 구멍 x 범위 (✅ 오른쪽=세계 -x 로 1mm 넓힘. 처음 ±6.8)
PK_UP = 2.0                                # ✅ 주머니를 위(안테나 쪽)로 2mm 길게 (배터리 모드는 TP4056 폭만큼 넓힘)
WIDEN_R = 1.0                              # ✅ 1판 테스트: 뒤(뚜껑 쪽)에서 봐서 오른쪽(= 세계 -x)으로 1mm 넓힘
DK_CX = -WIDEN_R / 2                       # DK 는 넓어진 주머니 가운데에 있다고 본다
OUT = Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)


def block(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, z0) * Box(
        x1 - x0, y1 - y0, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))


def silhouette(hw, y0, y1, r_top, r_bot, z0, z1, bumps=False):
    """머리 실루엣 (위 둥글게 r_top, 아래 r_bot) 을 z0~z1 로 민 것"""
    with BuildPart() as p:
        with BuildSketch(Plane.XY.offset(z0)) as sk:
            with Locations((0, (y0 + y1) / 2)):
                Rectangle(hw * 2, y1 - y0)
            top = sk.vertices().sort_by(Axis.Y)[-2:]
            bot = sk.vertices().sort_by(Axis.Y)[:2]
            fillet(top, r_top)
            fillet(sk.vertices().sort_by(Axis.Y)[:2], r_bot)
            if bumps:   # v6: 혹 없음
                pass
        extrude(amount=z1 - z0)
    return p.part


def mask(z0, z1, off=0.0, grow=False):
    """하트형 얼굴 (원 두 개 + 아래 둥근 사각) 을 off 만큼 키워서 z0~z1 로 민 것"""
    m = dict(MASK)
    if grow:   # ✅ 1판 결과: 얼굴판이 홈에 안 들어감 → 홈만 옆 +1mm(양쪽 0.5씩), 위 +2mm. 얼굴판은 원래 크기, 아래 끝 그대로
        m["hw"] += FACE_GROW_X / 2; m["rx"] += FACE_GROW_X / 2
        m["ey"] += FACE_GROW_TOP / 2; m["ry"] += FACE_GROW_TOP / 2
    with BuildPart() as p:
        with BuildSketch(Plane.XY.offset(z0)) as sk:
            with Locations((0, (m["y0"] + m["y1"]) / 2)):
                Rectangle(2 * (m["hw"] + off), m["y1"] - m["y0"] + 2 * off)
            fillet(sk.vertices().sort_by(Axis.Y)[:2], m["rb"] + off)
            for sx in (-1, 1):
                with Locations((sx * m["ex"], m["ey"])):
                    Ellipse(m["rx"] + off, m["ry"] + off)
        extrude(amount=z1 - z0)
    return p.part


def bx_to_x(bx):
    """보드 부품 면이 뒤(-z)를 향하므로, 뒤에서 본 왼쪽 = 세계 +x"""
    return DK_CX + DK[0] / 2 - bx


def build(battery):
    # 주머니 속 깊이(z): [배터리 칸] + DK
    BL = (max(LIPO[2], TP4056[2]) + FIT) if battery else 0.0
    PK_HW = max(PK_HW0, TP4056[0] / 2 + 0.3) if battery else PK_HW0
    PK_L = -PK_HW - WIDEN_R                    # 주머니 속 -x 끝 (+x 끝은 PK_HW 그대로)
    PCB_BACK = Z_FO - 0.2 - BL                 # DK PCB 뒷면(덮개 쪽)
    PCB_FRONT = PCB_BACK - DK_PCB              # 부품 면 시작
    DK_BACKMOST = PCB_BACK - DK_T              # 부품 가장 뒤
    Z_CI = DK_BACKMOST - 0.2                   # 뚜껑 안쪽 면
    Z_CO = Z_CI - WALL                         # 뚜껑 바깥 면
    DK_Y0 = Y_TOP - DK[1]                      # DK 아래 끝
    LIPO_Y1 = (Y_TOP - ANT_LEN) - 25.0         # 배터리 위 끝: 안테나에서 25mm 아래
    PK_Y0 = (min(DK_Y0, LIPO_Y1 - LIPO[1]) if battery else DK_Y0) - 0.3   # 주머니 속 바닥
    PK_Y1 = Y_TOP + 0.3 + PK_UP

    # ── 머리 (뒤가 열린 껍데기)
    head = silhouette(HEAD_W / 2, SAD, HEAD_TOP, R_TOP, R_BOT, Z_FI, Z_F, bumps=True)
    # 속 위 모서리: 터치 없으면 반지름 3 — OLED 위 모서리(폭 24.7)가 둥근 천장에 안 걸리게
    head -= silhouette(CAV_HW, SAD + FLOOR, CAV_TOP, (R_TOP - SIDE) if TOUCH_ON else 3.0, R_BOT - SIDE + 0.0, Z_FI - 1, Z_F - FRONT)
    # ✅ OLED 옆 헐거움 → 양옆 안쪽 벽에 레일 (겉모양 그대로). OLED 폭 + 0.2씩, 앞판에서 4mm 깊이
    for sx in (-1, 1):
        x0, x1 = sorted((sx * (OLED_PCB[0] / 2 + 0.2), sx * (CAV_HW + 0.5)))
        rail = block(x0, x1, SAD + FLOOR - 0.01, OLED_Y1, Z_F - FRONT - 4.0, Z_F - FRONT + 0.01)
        if BZ_IN > 0:   # 앞판이 뚫린 하트 자리 위에는 레일을 안 둠 (앞면이 베드라 허공에 뜸) → 위·아래 짧은 레일만 남음
            rail -= mask(Z_F - FRONT - 5, Z_F + 1, -BZ_LEDGE)
        head += rail
    for sx in (-1, 1):   # 날개 — 앞면부터 FLIP[5] 두께 (앞면이 베드라 서포트 없음)
        head += Pos(sx * FLIP[0], FLIP[1], Z_F - FLIP[5]) * Rot(0, 0, sx * FLIP[4]) * scale(
            Cylinder(1, FLIP[5], align=(Align.CENTER, Align.CENTER, Align.MIN)), by=(FLIP[2], FLIP[3], 1))
    if BZ_IN > 0:
        head -= mask(Z_F - BZ_IN, Z_F + 1, BZ_CLR, grow=True)                 # 얼굴 홈 (얼굴판 1.8 중 0.6 이 튀어나옴)
        head -= mask(Z_F - FRONT - 0.01, Z_F + 1, -BZ_LEDGE)                   # 홈 바닥(앞판)만 가운데 뚫기 → 턱만 남음
    for px, py in BZ_PINS:   # 얼굴판 자리 구멍 — 작아서 위 브리지 1.8mm 뿐
        head -= Pos(px, py, Z_F - 1.0) * Cylinder(0.9, 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    head -= block(-OLED_WIN[0] / 2, OLED_WIN[0] / 2, WIN_CY - OLED_WIN[1] / 2, WIN_CY + OLED_WIN[1] / 2 + WIN_TOP_ADD,
                  Z_F - FRONT - 1, Z_F + 1)
    # OLED 는 속 폭(29.2)에 PCB(27.3)가 꼭 맞게 들어가서 따로 턱 없이 폼테이프로 앞판에 붙인다
    # 터치: OLED 위 천장 밑에 패드가 위로 가게 눕힘 (뒤에서 밀어 넣음)
    TOUCH_Z = (Z_FI + Z_F - FRONT) / 2
    # 바닥 다월 구멍 (필라멘트 조각을 꽂아 고리와 자리를 맞춤)
    PEG = [(-9.0, (Z_FI + Z_F0) / 2), (9.0, (Z_FI + Z_F0) / 2)]
    for px, pz in PEG:
        head -= Pos(px, SAD - 0.01, pz) * Rot(-90, 0, 0) * Cylinder(DOWEL_R, 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    head = head.clean()

    bezel = mask(Z_F - BZ_IN, Z_F - BZ_IN + BZ_T)
    bezel -= block(-OLED_WIN[0] / 2, OLED_WIN[0] / 2, WIN_CY - OLED_WIN[1] / 2, WIN_CY + OLED_WIN[1] / 2 + WIN_TOP_ADD,
                   Z_F - BZ_IN - 1, Z_F + BZ_T + 1)
    for px, py in BZ_PINS:
        bezel += Pos(px, py, Z_F - 0.8) * Cylinder(0.7, 0.81, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # ── 걸이
    HW = HEAD_W / 2 - 1.0
    # 고리(clip) 는 따로 출력해 붙인다 (할로윈 펜던트 J 걸이처럼) — 안장 + 앞 립.
    # 윗면은 머리 바닥에, 뒷면은 뒷판 앞면에 붙고, 핀 2개가 머리 구멍에 들어가 자리를 잡는다.
    # 립 위치만 바꾼 틈 3종: 덮개 + 0.4 / 0.8 / 1.2 (헐거우면 미끄럼 패드·망치로 맞춤)
    def make_clip(lip_z):
        c = block(-HW, HW, 0, SAD, Z_FI, Z_F0 - 1.0)
        for sx in (-1, 1):   # 매달린 팔 (= 앞 립). 손은 납작한 타원
            x0, x1 = sorted((sx * ARM_X[0], sx * ARM_X[1]))
            c += block(x0, x1, -(ARM_L - 2.0), SAD, lip_z, lip_z + ARM_T)
            c += Pos(sx * sum(ARM_X) / 2, -(ARM_L - 2.0), lip_z) * scale(Cylinder(1, ARM_T, align=(Align.CENTER, Align.CENTER, Align.MIN)), by=(FOOT[0], FOOT[1], 1))
        for px, pz in PEG:
            c -= Pos(px, -1, pz) * Rot(-90, 0, 0) * Cylinder(DOWEL_R, SAD + 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
        return c.clean()
    clips = {g: make_clip(g - LID_T - PAD) for g in (LID_T + 0.4, LID_T + 0.8, LID_T + 1.2)}
    backplate = silhouette(HEAD_W / 2, SAD - 0.01, HEAD_TOP, R_TOP, R_BOT, Z_FO, Z_FI, bumps=True)     # 머리 뒤를 닫는 판
    backplate = backplate + block(PK_L - WALL, PK_HW + WALL, PK_Y0 - WALL, SAD, Z_FO, Z_FI)  # 덮개 뒤로 내려가는 앞벽
    pocket = block(PK_L - WALL, PK_HW + WALL, PK_Y0 - WALL, PK_Y1 + WALL, Z_CI, Z_FO + 0.01)
    POCKET_TIGHT = 0.1   # ✅ 뚜껑 헐거움 → 검정 주머니 속 폭만 합계 0.2mm 줄임 (뚜껑은 그대로)
    pocket -= block(PK_L + POCKET_TIGHT, PK_HW - POCKET_TIGHT, PK_Y0, PK_Y1, Z_CI - 1, Z_FO + 0.02)                        # 속 (뒤가 열림 → 뚜껑)
    hook = backplate + pocket
    # 아래 바닥: USB-C 가 빠져나가는 구멍 (가운데 전부) — DK 는 양옆 턱에 얹힌다
    hook -= block(USB_W[0], USB_W[1], PK_Y0 - WALL - 1, PK_Y0 + 0.01, Z_CI - 1, Z_FO + 0.02)
    # 위: OLED·터치 선 4+3 가닥이 머리 → 뒷판 구멍 → 주머니 윗면 홈 으로
    hook -= block(-7, 7, HOLE_Y[0], HOLE_Y[1], Z_FO - 1, Z_FI + 1)   # ✅ 선 구멍 14 폭 — OLED 핀헤더 바로 뒤로 올림: 듀폰 점퍼가 뒷판을 뚫고 뒤로 빠짐
    hook -= block(-7, 7, PK_Y1 - 0.5, PK_Y1 + WALL + 1, Z_CI - 0.5, Z_FO + 0.02)
    if battery:  # TP4056 충전 단자 구멍 (+x 옆벽)
        TP_CY = LIPO_Y1 + 1.0 + TP4056[1] / 2
        hook -= block(PK_HW - 1, PK_HW + WALL + 1, TP_CY - 5, TP_CY + 5, Z_FO - BL - 0.2, Z_FO + 0.02)
    hook = hook.clean()

    # ── 뚜껑 (버튼 구멍 + LED 창)
    cover = block(PK_L - WALL, PK_HW + WALL, PK_Y0 - WALL, PK_Y1 + WALL, Z_CO, Z_CI)
    cover -= block(USB_W[0], USB_W[1], PK_Y0 - WALL - 1, PK_Y0 + 0.3, Z_CO - 1, Z_CI + 1)              # USB-C 자리
    holes = {}
    for name, (bx, by) in [("LED", LED)]:   # ✅ 사용자: 버튼 구멍 3개(PA27·BOOT·RESET) 안 뚫음 — 버튼 안 누름. 굽기·리셋은 시리얼로
        x, y = bx_to_x(bx), Y_TOP - by
        r = 2.2 if name == "LED" else 2.0
        cover -= Pos(x, y, (Z_CO + Z_CI) / 2) * Cylinder(r, WALL * 3)
        holes[name] = (round(x, 1), round(y, 1))
    cover -= block(-4, 4, PK_Y1 - 0.5, PK_Y1 + WALL + 1, Z_CO - 1, Z_CI + 1)                   # 선 홈 이어짐
    # 끼움 턱: 뚜껑 안쪽 둘레에 0.8 폭 테. 주머니 벽 안에 꾹 끼워지고(틈 0.15),
    # 끝이 DK 기판 가장자리를 눌러 보드가 안 흔들린다. 나사 없음 — 손톱으로 빼면 열림
    RIM_W, RIM_D, RC = 0.8, (PCB_BACK - DK_PCB) - Z_CI - 0.05, 0.15
    rim = block(PK_L + RC, PK_HW - RC, PK_Y0 + RC, PK_Y1 - RC, Z_CI - 0.01, Z_CI + RIM_D)
    rim -= block(PK_L + RC + RIM_W, PK_HW - RC - RIM_W, PK_Y0 + RC + RIM_W, PK_Y1 - RC - RIM_W, Z_CI - 1, Z_CI + RIM_D + 1)
    rim -= block(USB_W[0], USB_W[1], PK_Y0 - 1, PK_Y0 + RC + RIM_W + 0.5, Z_CI - 1, Z_CI + RIM_D + 1)     # USB-C 자리
    rim -= block(-4, 4, PK_Y1 - RC - RIM_W - 0.5, PK_Y1 + 1, Z_CI - 1, Z_CI + RIM_D + 1)       # 선 자리
    cover = (cover + rim).clean()

    # ── 유령 (겹침·무게중심)
    G = {
        "oled": block(-OLED_PCB[0] / 2, OLED_PCB[0] / 2, OLED_Y0, OLED_Y1,
                      Z_F - FRONT - OLED_GLASS[2] - OLED_PCB[2], Z_F - FRONT - 0.05),
        # 기판(전체 면적) + 부품(가장자리 1.2 안쪽) — 뚜껑 턱이 기판 가장자리를 누를 자리
        "dk": block(DK_CX - DK[0] / 2, DK_CX + DK[0] / 2, DK_Y0, Y_TOP, PCB_BACK - DK_PCB, PCB_BACK)
              + block(DK_CX - DK[0] / 2 + 1.2, DK_CX + DK[0] / 2 - 1.2, DK_Y0 + 1.2, Y_TOP - 1.2, DK_BACKMOST, PCB_BACK - DK_PCB + 0.01),
    }
    if TOUCH_ON:
        G["touch"] = block(-TOUCH[0] / 2, TOUCH[0] / 2, CAV_TOP - 0.1 - TOUCH[2], CAV_TOP - 0.1,
                           TOUCH_Z - TOUCH[1] / 2, TOUCH_Z + TOUCH[1] / 2)
    if battery:
        G["lipo"] = block(-LIPO[0] / 2, LIPO[0] / 2, LIPO_Y1 - LIPO[1], LIPO_Y1, Z_FO - 0.2 - LIPO[2], Z_FO - 0.2)
        G["tp4056"] = block(-TP4056[0] / 2, TP4056[0] / 2, LIPO_Y1 + 1.0, LIPO_Y1 + 1.0 + TP4056[1],
                            Z_FO - 0.2 - TP4056[2], Z_FO - 0.2)
    laptop = block(-60, 60, -80, 0, -LID_T, 0)
    parts = {"head": head, "bezel": bezel, "hook": hook, "clip": clips[LID_T + 0.8], "cover": cover}
    info = {"holes": holes, "Z_CO": Z_CO, "DK_Y0": DK_Y0, "pcb_back": PCB_BACK, "lipo_top": LIPO_Y1 if battery else None, "clips": clips}
    return parts, G, laptop, info


NAMES = {"head": "머리", "bezel": "테두리", "hook": "뒷판·주머니", "clip": "고리", "cover": "뚜껑",
         "oled": "OLED", "touch": "터치", "dk": "Tiny DK", "lipo": "LiPo", "tp4056": "TP4056"}
PLA = 1.24e-3 * 0.85
MASS = {"oled": 3.0, "touch": 1.0, "dk": 4.0, "lipo": 5.5, "tp4056": 2.5, "wires": 2.0}   # ❓ 저울로 재면 바꾼다


def check(parts, G, laptop, title):
    print(f"\n========== {title} ==========")
    print("[겹침 검사]")
    bad = 0
    items = list(G.items()) + [("덮개", laptop)]
    for k, gh in items:
        for n, p in parts.items():
            inter = gh & p
            v = inter.volume if inter else 0.0
            if v > 1.0:
                bad += 1; print(f"  ⚠️ {NAMES.get(k, k)} ↔ {NAMES[n]} {v:.1f}mm³")
    ks = list(G)
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            inter = G[ks[i]] & G[ks[j]]
            v = inter.volume if inter else 0.0
            if v > 1.0:
                bad += 1; print(f"  ⚠️ {NAMES[ks[i]]} ↔ {NAMES[ks[j]]} {v:.1f}mm³")
    pn = list(parts)
    for i in range(len(pn)):
        for j in range(i + 1, len(pn)):
            inter = parts[pn[i]] & parts[pn[j]]
            v = inter.volume if inter else 0.0
            if v > 1.0:
                bad += 1; print(f"  ⚠️ {NAMES[pn[i]]} ↔ {NAMES[pn[j]]} {v:.1f}mm³")
    if not bad:
        print("  ✅ 1mm³ 넘는 겹침 없음")
    rows = [(NAMES[n], p.volume * PLA, p.center(CenterOf.MASS)) for n, p in parts.items()]
    rows += [(NAMES[k], MASS[k], g.center(CenterOf.MASS)) for k, g in G.items()]
    rows += [("선", MASS["wires"], G["dk"].center(CenterOf.MASS))]
    tot = sum(m for _, m, _ in rows)
    cz = sum(m * c.Z for _, m, c in rows) / tot
    print("[무게]")
    for n, m, c in rows:
        print(f"  {n:8s} {m:5.1f} g   (앞뒤 z={c.Z:6.1f}, 높이 y={c.Y:6.1f})")
    print(f"  합계     {tot:5.1f} g")
    print(f"[무게중심] z = {cz:.1f} mm  (덮개 {-LID_T:.1f} ~ 0) → "
          + ("✅ 덮개 위/뒤 — 앞으로 안 넘어감" if cz <= 0 else "⚠️ 화면 쪽"))
    allp = None
    for p in parts.values():
        allp = p if allp is None else allp + p
    bb = allp.bounding_box()
    hb = parts["head"].bounding_box()
    print(f"[외형] 전체 {bb.size.X:.1f} × {bb.size.Y:.1f} × {bb.size.Z:.1f} mm  "
          f"(덮개 위 {bb.max.Y:.1f}, 아래 {-bb.min.Y:.1f}) / 보이는 머리 {hb.size.X:.1f} × {hb.size.Y:.1f}")
    return allp, tot, cz, bb, hb


def bed(p):
    return Pos(0, 0, -p.bounding_box().min.Z) * p


results = {}
for battery, pre in ((False, "clip6"), (True, "clip6b")):
    parts, G, laptop, info = build(battery)
    allp, tot, cz, bb, hb = check(parts, G, laptop, "배터리 있음 (LiPo + TP4056)" if battery else "배터리 없음 (노트북 USB 전원) — 기본")
    ant_y = Y_TOP - ANT_LEN
    print(f"[안테나] 안테나 구간 y = {ant_y:.1f} ~ {Y_TOP:.1f} (덮개 윗모서리 0 보다 위 ✅)"
          + (f" / LiPo 위 끝 {info['lipo_top']:.1f} → 거리 {ant_y - info['lipo_top']:.1f} mm" if battery else ""))
    print(f"[구멍] 뚜껑: {info['holes']}")
    for k, p in parts.items():
        export_stl(p, str(OUT / f"{pre}_{k}.stl"))
    export_stl(bed(Rot(180, 0, 0) * parts["head"]), str(OUT / f"{pre}_head_print.stl"))   # 앞면이 베드
    export_stl(bed(Rot(180, 0, 0) * parts["bezel"]), str(OUT / f"{pre}_bezel_print.stl"))   # 앞면이 베드, 핀이 위
    export_stl(bed(parts["cover"]), str(OUT / f"{pre}_cover_print.stl"))   # 바깥면이 베드, 끼움 턱이 위
    export_stl(bed(Rot(0, 180, 0) * parts["hook"]), str(OUT / f"{pre}_hook_print.stl"))   # 앞면(머리 붙는 면 = 주머니 앞벽과 한 평면)이 베드
    for g, c in info["clips"].items():    # 고리: 안장 윗면을 베드에, 팔이 위로 자람 — 서포트 없음
        export_stl(bed(Rot(-90, 0, 0) * c), str(OUT / f"{pre}_clip_gap{g:.1f}_print.stl"))
    export_stl(allp, str(OUT / f"{pre}_body.stl"))
    for k, g in G.items():                 # 속 부품 (조립 화면용)
        export_stl(g, str(OUT / f"{pre}_g_{k}.stl"))
    export_stl(allp + laptop, str(OUT / f"{pre}_on_laptop.stl"))
    gsum = None
    for g in G.values():
        gsum = g if gsum is None else gsum + g
    export_stl(allp + gsum, str(OUT / f"{pre}_assembly.stl"))
    results[pre] = {
        "outer": [round(bb.size.X, 1), round(bb.size.Y, 1), round(bb.size.Z, 1)],
        "above": round(bb.max.Y, 1), "below": round(-bb.min.Y, 1),
        "head": [round(hb.size.X, 1), round(hb.size.Y, 1)],
        "weight": round(tot, 1), "comz": round(cz, 1),
        "screen": [0, round(GLASS_CY, 2), round(Z_F - FRONT + 0.05, 2)],
        "dk": {"size": [DK[0], DK[1], DK_T], "pos": [round(c, 2) for c in G["dk"].center(CenterOf.MASS).to_tuple()]},
    }
(OUT / "clip6_info.json").write_text(json.dumps(results, ensure_ascii=False))
print("\n[뷰어]", json.dumps(results, ensure_ascii=False))


# ═══════════════ 크기 테스트 조각 (본체 뽑기 전에 10~20분짜리로 치수 확인) ═══════════════
# out/test6_*.stl — 전부 서포트 없이 납작하게. 맞으면 본체 출력, 안 맞으면 상수만 고쳐 다시
parts, G, laptop, info = build(False)
DK_Y0_ = info["DK_Y0"]

# 2) 머리 앞쪽 5.6mm 만 (앞판 + OLED 자리 + 테두리 홈 + 혹 속 터치 칸 입구)
front = parts["head"] & block(-30, 30, -5, 50, Z_F - FRONT - 4.0, Z_F + 1)
export_stl(bed(Rot(180, 0, 0) * front), str(OUT / "test6_head_front.stl"))

# 3) 보드 주머니 아래쪽 12mm (DK 폭·두께·USB-C 구멍) — 위가 열려 있어 DK 를 꽂아 볼 수 있다
pk = parts["hook"] & block(-30, 30, DK_Y0_ - 5, DK_Y0_ + 12, -40, Z_FI + 0.01)
export_stl(bed(Rot(0, 180, 0) * pk), str(OUT / "test6_pocket_bottom.stl"))   # 앞면이 베드 (본체와 같은 자세)
# 뚜껑은 원래 1.6g 이라 그대로 테스트 (DK 위에 대 보고 버튼·LED 구멍 위치 확인)
print("[테스트 조각] out/test6_head_front / test6_pocket_bottom")
print(f"  무게: 머리 앞 {front.volume*PLA:.1f}g, 주머니 {pk.volume*PLA:.1f}g")
