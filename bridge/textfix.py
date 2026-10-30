"""화면에 그리기 전에 글자 다듬기 — 애플 SD 산돌고딕에 없는 글자는 엑스친 네모(□)로 나와서
  𝗣𝗟𝗔𝗬𝗟𝗜𝗦𝗧 같은 '굵은 수학 글자'는 보통 글자로 바꾸고 (NFKC), 이모지처럼 글꼴에 없는 건 뺀다"""
import re, unicodedata
from fontTools.ttLib import TTCollection

F = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
_CMAP = set(TTCollection(F)[6].getBestCmap())


def _fix(ch):
    if ord(ch) in _CMAP or ch in " \n":
        return ch
    n = unicodedata.normalize("NFKC", ch)              # 글꼴에 없을 때만 바꿈 (ㅋㅋ 같은 자모는 그대로 두려고)
    return n if n and all(ord(c) in _CMAP for c in n) else " "


def clean(text):
    t = "".join(_fix(ch) for ch in unicodedata.normalize("NFC", text or ""))
    return re.sub(r"[ \t]+", " ", t).strip()
