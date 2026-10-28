#!/bin/zsh
# 촬영용 연속 시연. 사용: ./show.sh        (한 바퀴, 약 1분 40초)
#                       ./show.sh loop   (Ctrl+C 로 멈출 때까지 반복)
# 평소 돌던 연결 프로그램(자동 실행)을 잠깐 멈추고, 끝나면 다시 켬
cd "$(dirname "$0")"
U=gui/$(id -u)/com.nucode.breadpet
launchctl bootout $U 2>/dev/null; pkill -f notify_bridge.py 2>/dev/null; sleep 1
trap 'launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.nucode.breadpet.plist 2>/dev/null; echo "(연결 프로그램 다시 켬)"' EXIT
python3 -u notify_bridge.py --show ${1:+--loop}
