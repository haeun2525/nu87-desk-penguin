#!/bin/zsh
# NU87 Tiny DK 에 버튼 없이 굽기: 시리얼 'u' → UART 굽기 모드 → 업로드 → RTS 로 리셋
# 사용: ./upload_nu87.sh desk_pet   (스케치가 'u' 처리를 갖고 있어야 함. 처음 한 번은 BOOT+RESET 수동)
set -e
launchctl bootout gui/$(id -u)/com.nucode.breadpet 2>/dev/null || true; pkill -f notify_bridge.py 2>/dev/null || true   # 맥 연결 프로그램이 포트를 잡고 있으면 못 구움
trap 'launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.nucode.breadpet.plist 2>/dev/null' EXIT
SK=${1:-desk_pet}; P=${PORT:-$(ls /dev/cu.usbserial* | head -1)}
A="/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli"
python3 -c "
import serial,time
s=serial.Serial(); s.port='$P'; s.baudrate=115200; s.dtr=False; s.rts=False; s.open(); time.sleep(1.5); s.write(b'u'); time.sleep(1); s.close()"  # 포트 열면 보드가 리셋됨 → 부팅 기다린 뒤 'u'
"$A" compile -u -p "$P" --fqbn "realtek:AmebaD:Ameba_AMB26:AutoUploadMode=Disable" "$SK" | grep -E "successfully|error|Error" || true
python3 -c "
import serial,time
s=serial.Serial(); s.port='$P'; s.baudrate=115200; s.dtr=False; s.rts=False; s.timeout=0.2; s.open()
s.rts=True; time.sleep(0.15); s.rts=False
t=time.time(); o=b''
while time.time()-t<4: o+=s.read(512)
print(o.decode('utf-8','replace'))"
