#!/bin/zsh
# 촬영용: 알림 장면만 (엄마 → 채널 춘식이 + 내용 → 메일 주소 + 내용)
cd "$(dirname "$0")"
launchctl bootout gui/$(id -u)/com.nucode.breadpet 2>/dev/null; pkill -f notify_bridge.py 2>/dev/null; sleep 1
trap 'launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.nucode.breadpet.plist 2>/dev/null' EXIT
python3 -u notify_bridge.py --alerts
