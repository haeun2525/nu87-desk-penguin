"""알림 말고 펫이 보여주는 것들 — 각 함수는 몇 초마다 불리고, 보여줄 게 있으면 (화면, 'h' 여부) 를 돌려줌

  music    크롬 유튜브 / 유튜브 뮤직 탭 제목이 바뀌면 ♪ 화면
  calendar 구글 캘린더 비밀 iCal 주소(~/.breadpet/config.json 의 gcal_ics) → 일정 10분 전, 시작할 때
  stretch  맥을 50분 계속 쓰면 기지개 화면 (5분 이상 손 떼면 처음부터)
  claude   Claude Code 훅이 남기는 ~/.breadpet/claude_start / claude_stop → 2분 넘게 걸린 작업이 끝나면
  rain     2시간 안에 비 확률 60% 이상이면 우산 화면 (3시간에 한 번만)
"""
import json, os, re, subprocess, time, urllib.request
from datetime import datetime, timedelta, timezone

import screens

HOME = os.path.expanduser("~/.breadpet")
CONFIG = os.path.join(HOME, "config.json")


def config():
    try:
        return json.load(open(CONFIG))
    except Exception:
        return {}


# ─────────────── 음악 (유튜브) ───────────────
# 크롬 "보기 > 개발자 > Apple Events의 자바스크립트 허용" 이 켜져 있어야 재생 중인지·채널·챕터를 읽음
# (꺼져 있으면 탭 제목만 보고, 재생 여부는 모름)
_JS = (r"(()=>{const q=s=>document.querySelector(s);const v=q('video');"
       r"const m=location.host.startsWith('music.');"
       r"const t=m?q('ytmusic-player-bar .title'):q('ytd-watch-metadata h1');"
       r"const c=m?q('ytmusic-player-bar .byline'):q('ytd-watch-metadata #channel-name a');"
       r"const cc=q('.ytp-chapter-container');"
       r"const ch=cc&&cc.offsetParent!==null&&getComputedStyle(cc).display!=='none'?q('.ytp-chapter-title-content'):null;"
       r"return JSON.stringify({p:!!v&&!v.paused,t:t?t.textContent.trim():'',"
       r"c:c?c.textContent.trim().split('•')[0].trim():'',ch:ch?ch.textContent.trim():''})})()")
_AS_TABS = """
set out to ""
set TB to (ASCII character 9)
tell application "Google Chrome"
  repeat with w in windows
    repeat with t in tabs of w
      set u to URL of t
      if u contains "music.youtube.com" or u contains "youtube.com/watch" then
        try
          set r to execute t javascript "%s"
        on error
          set r to "NOJS"
        end try
        set out to out & u & TB & (title of t) & TB & r & linefeed
      end if
    end repeat
  end repeat
end tell
return out""" % _JS.replace("\\", "\\\\").replace('"', '\\"')
_last_song = None
_music_started = False


def _chrome_running():
    r = subprocess.run(["pgrep", "-x", "Google Chrome"], capture_output=True)
    return r.returncode == 0


def clean_title(url, title):
    title = re.sub(r"^\(\d+\)\s*", "", title)                  # (3) 같은 알림 수
    title = re.sub(r"\s*-\s*YouTube( Music)?$", "", title)
    if "music.youtube.com" in url and title in ("YouTube Music", ""):
        return None                                           # 재생 안 하는 홈 화면
    return title.strip() or None


def now_playing():
    """(곡, 부제) 또는 None — 재생 중인 탭 우선"""
    if not _chrome_running():
        return None
    r = subprocess.run(["osascript", "-e", _AS_TABS], capture_output=True, text=True, timeout=8)
    fallback = None
    for line in r.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        url, title, js = parts[0], parts[1], "\t".join(parts[2:])
        if js == "NOJS":                                       # 자바스크립트 허용 꺼짐 → 제목만
            t = clean_title(url, title)
            if t and not fallback: fallback = (t, "유튜브")
            continue
        try:
            info = json.loads(js)
        except ValueError:
            continue
        if not info.get("p"):
            continue                                           # 멈춘 탭은 무시
        if info.get("ch", "").lower() in ("in this video", "이 동영상", "동영상 내 챕터"):
            info["ch"] = ""                                    # 챕터 없는 영상의 자리표시 글자
        song = info.get("ch") or info.get("t") or clean_title(url, title)
        sub = info.get("c") or "유튜브"
        if info.get("ch") and info.get("t"):                   # 모음 영상: 챕터 = 곡, 부제 = 영상 제목
            sub = info["t"]
        if song:
            return song, sub
    return fallback


def music():
    global _last_song, _music_started
    np = now_playing()
    song = np[0] if np else None
    if not _music_started:                                     # 처음 켰을 때는 지금 곡을 기억만
        _music_started = True; _last_song = song
        return None
    if not song or song == _last_song:
        if np is None: _last_song = None if song is None else _last_song
        return None
    _last_song = song
    return screens.screen("music", song, np[1], 1, title_lines=2), False   # 곡 제목 2줄, 채널 1줄


# ─────────────── 구글 캘린더 (비밀 iCal 주소) ───────────────
_cal = {"events": [], "fetched": 0}
_cal_done = set()


def _fetch_calendar(url):
    import icalendar, recurring_ical_events
    data = urllib.request.urlopen(url, timeout=15).read()
    cal = icalendar.Calendar.from_ical(data)
    now = datetime.now(timezone.utc)
    evs = []
    for e in recurring_ical_events.of(cal).between(now - timedelta(hours=1), now + timedelta(days=1)):
        start = e.get("DTSTART").dt
        if not isinstance(start, datetime):
            continue                                          # 종일 일정은 건너뜀
        if start.tzinfo is None:
            start = start.astimezone()
        evs.append((start, str(e.get("SUMMARY", "일정")), str(e.get("UID", "")) + start.isoformat()))
    return evs


def calendar():
    url = config().get("gcal_ics")
    if not url:
        return None
    if time.time() - _cal["fetched"] > 600:
        try:
            _cal["events"] = _fetch_calendar(url); _cal["fetched"] = time.time()
        except Exception as e:
            print("[calendar] 가져오기 실패:", e); _cal["fetched"] = time.time() - 480
    now = datetime.now(timezone.utc)
    for start, title, uid in _cal["events"]:
        mins = (start - now).total_seconds() / 60
        for key, lo, hi, label in ((uid + ":10", 9, 10.5, "10분 뒤"), (uid + ":0", -1, 0.5, "지금 시작")):
            if lo <= mins <= hi and key not in _cal_done:
                _cal_done.add(key)
                return screens.screen("calendar", f"{label} {start.astimezone():%H:%M}", title, 2), False
    return None


# ─────────────── 스트레칭 ───────────────
STRETCH_AFTER = 50 * 60
BREAK_IDLE = 5 * 60
_active_since = None


def idle_seconds():
    out = subprocess.run(["ioreg", "-c", "IOHIDSystem"], capture_output=True, text=True).stdout
    m = re.search(r'"HIDIdleTime" = (\d+)', out)
    return int(m.group(1)) / 1e9 if m else 0


def stretch():
    global _active_since
    now = time.time()
    if idle_seconds() >= BREAK_IDLE:
        _active_since = None
        return None
    if _active_since is None:
        _active_since = now
    if now - _active_since >= STRETCH_AFTER:
        mins = int((now - _active_since) / 60)
        _active_since = now                                    # 다음 알림은 또 50분 뒤
        return screens.screen("stretch", "기지개 펴요!", f"{mins}분째 일하는 중"), False
    return None


# ─────────────── Claude 작업 끝 ───────────────
CLAUDE_MIN = 120
_claude_seen = None


def _read_ts(name):
    try:
        return int(open(os.path.join(HOME, name)).read().strip())
    except Exception:
        return None


def claude():
    global _claude_seen
    stop = _read_ts("claude_stop")
    if stop is None or stop == _claude_seen:
        return None
    first = _claude_seen is None
    _claude_seen = stop
    start = _read_ts("claude_start")
    if first or start is None or stop - start < CLAUDE_MIN:
        return None
    mins = max(1, round((stop - start) / 60))
    return screens.screen("check", "Claude 작업 끝!", f"{mins}분 걸렸어요"), True


# ─────────────── 비 오기 전 ───────────────
RAIN_POP = 60
_rain = {"checked": 0, "warned": 0}


def rain():
    if time.time() - _rain["checked"] < 900 or time.time() - _rain["warned"] < 3 * 3600:
        return None
    _rain["checked"] = time.time()
    import weather
    try:
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={weather.LAT}&longitude={weather.LON}"
               "&hourly=precipitation_probability&timezone=Asia%2FSeoul&forecast_hours=3")
        j = json.load(urllib.request.urlopen(url, timeout=10))
        pops = j["hourly"]["precipitation_probability"][:3]
    except Exception as e:
        print("[rain] 실패:", e); return None
    if max(pops) >= RAIN_POP:
        _rain["warned"] = time.time()
        return screens.screen("umbrella", "우산 챙겨요", f"2시간 안에 비 {max(pops)}%"), False
    return None


ALL = [("claude", claude), ("calendar", calendar), ("music", music), ("stretch", stretch), ("rain", rain)]


# ─────────────── 지메일: 맨 위 안 읽은 메일의 주소·제목 (지메일 탭에서) ───────────────
# 크롬 알림에는 보낸 사람 '이름'만 와서, 주소는 열려 있는 지메일 탭 목록에서 읽음
_GMAIL_JS = (r"(()=>{const r=document.querySelector('tr.zA.zE')||document.querySelector('tr.zA');if(!r)return '';"
             r"const e=r.querySelector('span[email]');const s=r.querySelector('span.bog');"
             r"return JSON.stringify({e:e?e.getAttribute('email'):'',n:e?(e.getAttribute('name')||e.textContent):'',s:s?s.textContent.trim():''})})()")
_AS_GMAIL = """
tell application "Google Chrome"
  repeat with w in windows
    repeat with t in tabs of w
      if URL of t contains "mail.google.com" then
        try
          return execute t javascript "%s"
        end try
      end if
    end repeat
  end repeat
end tell
return \"\"""" % _GMAIL_JS.replace("\\", "\\\\").replace('"', '\\"')


def gmail_top():
    """{'e': 주소, 'n': 이름, 's': 제목} 또는 None"""
    if not _chrome_running():
        return None
    r = subprocess.run(["osascript", "-e", _AS_GMAIL], capture_output=True, text=True, timeout=8)
    try:
        return json.loads(r.stdout.strip()) if r.stdout.strip() else None
    except ValueError:
        return None
