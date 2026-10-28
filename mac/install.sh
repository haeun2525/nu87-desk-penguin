#!/bin/zsh
# 맥 연결 프로그램(bridge)을 로그인할 때 자동으로 켜지게 등록. 끄기: ./install.sh off
set -e
L=com.nucode.breadpet; PL=~/Library/LaunchAgents/$L.plist
BR="$(cd "$(dirname "$0")/../bridge" && pwd)"
launchctl bootout gui/$(id -u)/$L 2>/dev/null || true
if [[ "$1" == off ]]; then rm -f $PL; echo "자동 실행 끔"; exit; fi
mkdir -p ~/.breadpet ~/Library/LaunchAgents
cat > $PL <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$L</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/python3</string><string>-u</string><string>$BR/notify_bridge.py</string>
  </array>
  <key>WorkingDirectory</key><string>$BR</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>10</integer>
  <key>StandardOutPath</key><string>$HOME/.breadpet/bridge.log</string>
  <key>StandardErrorPath</key><string>$HOME/.breadpet/bridge.log</string>
</dict></plist>
PLIST
launchctl bootstrap gui/$(id -u) $PL
echo "자동 실행 등록 — 로그: ~/.breadpet/bridge.log"
