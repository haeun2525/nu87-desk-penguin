#!/bin/zsh
# 촬영용 알림 장면
#   ./alerts.sh                        예시 장면 (엄마 → 채널 춘식이 + 내용 → 메일 주소 + 내용)
#   ./alerts.sh 춘식이                  실제로 왔던 알림 중 이름에 '춘식이' 들어간 마지막 6개를 그대로 다시
#   ./alerts.sh "축하하는 춘식이" "내용1" "내용2"   직접 적은 내용으로 (같은 사람이 이어 보낸 것처럼)
#   ./alerts.sh -                      실제로 왔던 마지막 알림 6개
cd "$(dirname "$0")"
launchctl bootout gui/$(id -u)/com.nucode.breadpet 2>/dev/null; pkill -f notify_bridge.py 2>/dev/null; sleep 1
trap 'launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.nucode.breadpet.plist 2>/dev/null' EXIT
if [[ $# -eq 0 ]]; then python3 -u notify_bridge.py --alerts
elif [[ $1 == - ]]; then python3 -u notify_bridge.py --replay
else python3 -u notify_bridge.py --replay "$@"; fi
