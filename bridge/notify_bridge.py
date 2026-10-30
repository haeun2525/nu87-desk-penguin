#!/usr/bin/env python3
"""맥 알림 → 식빵 펫 (NU87, firmware/desk_pet)

맥 알림 센터 기록(db)에 새 알림이 쌓이면 USB 시리얼로 보드에 한 글자 보낸다.
  카카오톡 알림                         → 'k'
  Chrome 알림 중 mail.google.com 에서 온 것 → 'g'  (지메일 설정 > 데스크톱 알림 켜기, 지메일 탭은 열어 둬야 함)

날씨: 30분마다 'p' + 1024바이트(128×64 화면) 로 날씨 화면을 보냄 (Open-Meteo, 삼성동)

사용: python3 notify_bridge.py         (Ctrl+C 로 끔)
      python3 notify_bridge.py --weather  (날씨 화면 지금 한 번 보내기)
      python3 notify_bridge.py --demo     (음악·일정·스트레칭·Claude·우산 화면을 차례로 보내 보기)
그 밖의 화면(음악·구글 캘린더·스트레칭·Claude 작업 끝·비 예보)은 features.py
      python3 notify_bridge.py --test  (보드에 'k' → 'g' 한 번씩 보내 보기)
보내는 것: 'n' + 'k'/'g' + 보낸 사람 이름 그림(128×16, 256바이트) → 5초 뒤 내용 화면('p') 1~2장
  카톡: 보낸 사람(단톡이면 방 이름) + 메시지 앞부분   지메일: 메일 주소 + 제목 (지메일 탭 목록에서 읽음)
  내용 끄기: ~/.breadpet/config.json 에 "show_content": false  (책상 옆 사람에게 보일 수 있음)
"""
import glob, plistlib, sqlite3, subprocess, sys, time
import serial
from name_bitmap import render, to_bytes, text_width, render_wide, to_bytes_w
import weather
import features, screens

WEATHER_EVERY = 30 * 60

DB = glob.os.path.expanduser("~/Library/Group Containers/group.com.apple.usernoted/db2/db")
KAKAO = "com.kakao.kakaotalkmac"
CHROME = "com.google.chrome.framework.alertnotificationservice"
POLL = 1.5


def front_seen():
    """지금 맨 앞 창이 카톡이면 'k', 크롬의 지메일 탭이면 'g' — 사용자가 확인한 걸로 보고 보드 표시를 지움"""
    try:
        asn = subprocess.run(["lsappinfo", "front"], capture_output=True, text=True, timeout=3).stdout.strip()
        bid = subprocess.run(["lsappinfo", "info", "-only", "bundleid", asn], capture_output=True, text=True, timeout=3).stdout
    except Exception:
        return None
    if "com.kakao.KakaoTalkMac" in bid or KAKAO in bid.lower():
        return "k"
    if "com.google.Chrome" in bid:
        r = subprocess.run(["osascript", "-e", 'tell application "Google Chrome" to get URL of active tab of front window'],
                           capture_output=True, text=True, timeout=3)
        if "mail.google.com" in r.stdout:
            return "g"
    return None


def find_port():
    ports = glob.glob("/dev/cu.usbserial*")
    return ports[0] if ports else None


def open_board():
    while True:
        p = find_port()
        if p:
            try:
                s = serial.Serial()
                s.port, s.baudrate, s.timeout = p, 115200, 0
                s.dtr = False; s.rts = False   # Tiny DK: RTS 가 리셋이라 꺼진 채로 연다
                s.open()
                print(f"[bridge] 보드 연결: {p}")
                return s
            except serial.SerialException:
                pass
        print("[bridge] 보드 기다리는 중 (USB 꽂기)…")
        time.sleep(3)


def send(board, k, name):
    if name and text_width(name) > 124:           # 긴 이름(메일 주소) → 보드가 옆으로 흘림
        img, w = render_wide(name)
        data = b"N" + k.encode() + bytes([w & 0xFF, w >> 8]) + to_bytes_w(img)
        for i in range(0, len(data), 64):
            board.write(data[i:i + 64]); board.flush(); time.sleep(0.02)
    elif name:
        data = b"n" + k.encode() + to_bytes(render(name))
        for i in range(0, len(data), 64):      # 한 번에 258바이트를 보내면 보드 수신 버퍼가 넘쳐 알림이 사라짐 → 나눠 보냄
            board.write(data[i:i + 64]); board.flush(); time.sleep(0.02)
    else:
        board.write(k.encode())


def send_picture(board, img):
    data = b"p" + weather.to_bytes(img)
    for i in range(0, len(data), 64):          # 보드 수신 버퍼가 작아서 나눠 보냄
        board.write(data[i:i + 64]); board.flush(); time.sleep(0.02)


def send_weather(board):
    try:
        img, w, label = weather.render()
        send_picture(board, img)
        print(time.strftime("%H:%M:%S"), f"→ 날씨 {round(w['t'])}° {label}")
    except Exception as e:
        print("[bridge] 날씨 가져오기 실패:", e)


MAIL_ADDR = "demoday.team@nucoders-study.kr"   # 촬영용 예시 주소


def show(board, loop=False, only_alerts=False):
    """촬영용: 할 수 있는 걸 차례로 (약 1분 40초). 화면 하나 = 8초, 알림 = 5초"""
    def say(msg):
        print(time.strftime("%H:%M:%S"), msg, flush=True)
    time.sleep(2); board.read(1000)
    while True:
        say("① 평소엔 잠"); time.sleep(5)
        say("② 카톡 알림 — 엄마"); send(board, "k", "엄마"); time.sleep(5.5)
        say("③ 카톡 알림 — 채널 춘식이 → 내용")
        send(board, "k", "채널 춘식이"); time.sleep(5)
        for img in screens.message_pages("k", "채널 춘식이", "[광고] 춘식이 굿즈 최대 50% 할인! 오늘 자정까지만~ 지금 바로 확인해 보세요"):
            send_picture(board, img); time.sleep(6)
        say("④ 메일 알림 — 메일 주소(옆으로 흐름) → 내용")
        send(board, "g", MAIL_ADDR); time.sleep(1.4 + max(0, text_width(MAIL_ADDR) + 4 - 124) / 30 + 1.5)
        for img in screens.message_pages("g", "데모데이 운영팀", "[안내] 12/4 데모데이 리허설 일정과 발표 순서를 공유드립니다"):
            send_picture(board, img); time.sleep(6)
        if only_alerts:
            break
        np = None
        try: np = features.now_playing()
        except Exception: pass
        song, sub = np if np else ("Colde - 와르르", "Colde")
        say(f"⑤ 지금 듣는 음악 — {song}"); send_picture(board, screens.screen("music", song, sub, 2)); time.sleep(9)
        say("⑥ 스트레칭"); send_picture(board, screens.screen("stretch", "기지개 펴요!", "52분째 일하는 중")); time.sleep(9)
        try: wimg = weather.render()[0]              # 날씨는 미리 받아 둠 (받는 동안 틈이 안 생기게)
        except Exception: wimg = screens.screen("umbrella", "날씨", "가져오기 실패")
        say("⑦ 날씨 → 우산 (이어서)"); send_picture(board, wimg); time.sleep(7.5)   # 8초 끝나기 전에 다음 화면 → 얼굴 안 비침
        send_picture(board, screens.screen("umbrella", "우산 챙겨요", "2시간 안에 비 70%")); time.sleep(9)
        say("⑧ 일정 10분 전 → Claude 작업 끝 → 좋아함 (이어서)")
        send_picture(board, screens.screen("calendar", "10분 뒤 15:00", "누코드 주간회의")); time.sleep(7.5)
        send_picture(board, screens.screen("check", "Claude 작업 끝!", "12분 걸렸어요")); time.sleep(7.5)
        board.write(b"h"); time.sleep(5)
        say("⑨ 다시 잠 (구석에 안 읽은 알림 아이콘)"); time.sleep(8)
        if not loop:
            break
        board.write(b"t"); time.sleep(6)   # 다음 바퀴 전에 구석 아이콘 지움
    say("끝")


def content_pages(k, name, body):
    """알림 뒤에 이어 보여줄 내용 화면들"""
    if not features.config().get("show_content", True):
        return []
    if k == "k":
        return screens.message_pages("k", name, body)
    top = None
    try: top = features.gmail_top()
    except Exception: pass
    addr = (top or {}).get("e") or name
    subj = (top or {}).get("s") or (body.splitlines()[0] if body else "")
    return screens.message_pages("g", (top or {}).get("n") or addr, subj)


def notify_with_content(board, k, name, body, wait=time.sleep):
    """알림 애니메이션(5초) → 내용 화면 (한 장당 5초)"""
    send(board, k, name)
    for img in content_pages(k, name, body):
        wait(5); send_picture(board, img)


def max_id(c):
    return c.execute("select coalesce(max(rec_id), 0) from record").fetchone()[0]


def new_events(c, after):
    rows = c.execute(
        "select r.rec_id, a.identifier, r.data from record r join app a on a.app_id = r.app_id "
        "where r.rec_id > ? order by r.rec_id", (after,)).fetchall()
    out = []
    for rid, ident, data in rows:
        try:
            req = plistlib.loads(data).get("req", {})
        except Exception:
            req = {}
        name = (req.get("titl") or "").strip()
        body = (req.get("body") or "").strip()
        if ident == KAKAO:
            out.append((rid, "k", name, body))
        elif ident == CHROME and "mail.google.com" in (req.get("subt") or ""):
            out.append((rid, "g", name, body))
    return out, (rows[-1][0] if rows else after)


def main():
    board = open_board()
    if "--weather" in sys.argv:
        time.sleep(2)
        send_weather(board); time.sleep(1)
        print(board.read(200).decode("utf-8", "replace").strip())
        return
    if "--alerts" in sys.argv:
        show(board, only_alerts=True)
        return
    if "--show" in sys.argv:
        show(board, loop="--loop" in sys.argv)
        return
    if "--demo" in sys.argv:
        time.sleep(2)
        demos = [screens.screen("music", "Colde - 와르르", "오프온오프 노래 모음"),
                 screens.screen("calendar", "10분 뒤 15:00", "누코드 주간회의"),
                 screens.screen("stretch", "기지개 펴요!", "52분째 일하는 중"),
                 screens.screen("check", "Claude 작업 끝!", "12분 걸렸어요"),
                 screens.screen("umbrella", "우산 챙겨요", "2시간 안에 비 70%")]
        for i, img in enumerate(demos):
            send_picture(board, img); print("[demo]", i + 1); time.sleep(9)
            if i == 3: board.write(b"h"); time.sleep(4)
        return
    if "--test" in sys.argv:
        time.sleep(2)   # 포트 열면 보드가 리셋될 수 있어서 부팅 기다림
        for k, name in (("k", "엄마"), ("g", "누코드 스터디")):
            send(board, k, name); print("[test] 보냄", k, name); time.sleep(6)
        return
    c, last, next_db = None, None, 0
    print("[bridge] 알림 기다리는 중 (카톡 / 지메일), 날씨는 30분마다")
    next_weather = time.time() + 5
    next_feat = 0
    unread = {}         # 보드 구석에 떠 있는 표시 {'k'/'g': 뜬 시각} — 카톡 창·지메일 탭을 보면 지움 (보드도 5분 뒤 스스로 지움)
    queue = []          # (보낼 시각, 데이터) — 화면이 8초 떠 있으니 겹치지 않게 줄 세움
    while True:
        try:
            now = time.time()
            if now >= next_feat:
                next_feat = now + 5
                for name, fn in features.ALL:
                    try:
                        r = fn()
                    except Exception as e:
                        print(f"[{name}] 오류:", e); r = None
                    if r:
                        img, happy = r
                        t0 = max([t for t, _ in queue] + [now]) + (9 if queue else 0)
                        queue.append((t0, ("p", img)))
                        if happy: queue.append((t0 + 8.5, ("h", None)))
                        print(time.strftime("%H:%M:%S"), "→", name)
            while queue and queue[0][0] <= time.time():
                _, (kind, img) = queue.pop(0)
                if kind == "p": send_picture(board, img)
                else: board.write(b"h")
            if time.time() >= next_weather:
                send_weather(board); next_weather = time.time() + WEATHER_EVERY
            if c is None and time.time() >= next_db:   # 알림 db 는 '전체 디스크 접근' 권한이 있어야 열림
                next_db = time.time() + 60
                try:
                    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True); last = max_id(c)
                    print("[bridge] 알림 db 열림")
                except sqlite3.Error as e:
                    c = None
                    print("[bridge] 알림 db 못 엶 (전체 디스크 접근 권한 필요):", e)
            evs = []
            if c is not None:
                evs, last = new_events(c, last)
            for _, k, name, body in evs:
                if k == "g":                           # 메일은 이름 대신 주소
                    try: name = (features.gmail_top() or {}).get("e") or name
                    except Exception: pass
                send(board, k, name); unread[k] = time.time()
                t = time.time()
                for img in content_pages(k, name, body):
                    t += 5; queue.append((t, ("p", img)))
                queue.sort(key=lambda q: q[0])
                print(time.strftime("%H:%M:%S"), "→", "카톡" if k == "k" else "지메일", name)
                time.sleep(0.3)
            unread = {k: t for k, t in unread.items() if time.time() - t < 300}
            if unread:
                seen = front_seen()
                if seen in unread:
                    board.write(seen.upper().encode()); unread.pop(seen)
                    print(time.strftime("%H:%M:%S"), "→ 확인함, 표시 지움:", "카톡" if seen == "k" else "지메일")
            board.read(256)   # 보드 로그 버리기
        except serial.SerialException:
            print("[bridge] 보드 끊김"); board = open_board()
        except sqlite3.Error as e:
            print("[bridge] db 읽기 실패:", e); c = None; time.sleep(5)
        time.sleep(POLL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
