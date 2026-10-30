/*
 * 데스크 펭귄 펫 (NU87 Tiny DK + SSD1306 OLED) — 얼굴 + 노트북 알림
 *
 * ★ 2단계에서 더한 것
 *   - 시리얼 'k' = 카톡 알림, 'g' = 지메일 알림 (맥의 bridge/notify_bridge.py 가 보냄)
 *     'n' + 'k'/'g' + 256바이트 = 보낸 사람 이름 그림(128×16, 한 줄 16바이트, 왼쪽이 MSB) 과 함께 알림
 *     (보드에 한글 글꼴이 없어서 맥이 이름을 그림으로 그려 보냄)
 *     'N' + 'k'/'g' + 글자폭(2바이트, 작은 쪽 먼저) + 512바이트 = 긴 이름(메일 주소 등) 256×16 → 옆으로 흘려 보여줌
 *     'p' + 1024바이트 = 맥이 그린 화면 한 장(128×64) 을 8초 보여줌 — 날씨 같은 정보 화면
 *     → 놀란 얼굴 + 말풍선/봉투 아이콘이 통통 튐 4초 → 평소 얼굴로 돌아가도 구석에 작은 아이콘이 5분 남음
 *   - 구석 아이콘은 5분 뒤 저절로 사라짐. 터치(TTP223 → PA28, 정수리) / 't' 로도 지움
 *     'K' / 'G' = 카톡 / 메일 표시만 지움 (맥에서 카톡 창·지메일 탭을 앞으로 띄우면 bridge 가 보냄)
 *   - 평소엔 잠 (깜빡임이 업무에 방해 → 사용자 요청). 알림·터치 때만 깼다가 4초 뒤 다시 잠
 *   - 'h' = Claude 작업 끝 → 4초 동안 좋아함
 *   - 잠자다 알림 오면 깸
 *
 * ★ 지금 되는 것
 *   - 버디 얼굴 (꽉 찬 둥근사각 눈 + 작은 대칭 미소) — 시뮬레이터 core/styles.js 의 buddy 와 같은 치수
 *   - 2~5초마다 깜빡임, 가끔 두리번
 *   - 터치(또는 보드 S1 버튼) → 좋아함 (^^ 눈 + 벌린 입, 통통 튐) 1.8초
 *   - 45초 아무도 안 만지면 → 잠 (감은 눈 + z, 숨쉬듯 들썩). 터치하면 "음..?" 하고 깸
 *
 * ★ 보드 두 가지 다 된다 (컴파일할 때 보드를 고르면 핀이 알아서 바뀜)
 *   NU40-DK  (nRF52840)  FQBN nucode:nrf52:nu40dk
 *     OLED SDA → P0.26 (우측 25) / SCL → P0.27 (우측 26) / 터치 TTP223 OUT → P0.28 (좌측 5, 가안)
 *     TTP223 을 아직 안 달았으면 보드의 S1 버튼(P0.11)을 누르면 똑같이 터치로 친다.
 *   NU87 Tiny DK (RTL8720DF)  FQBN realtek:AmebaD:Ameba_AMB26
 *     OLED SDA → PA26 / SCL → PA25 (보드 기본 I2C) / 터치 TTP223 OUT → PA28 (가안)
 *     TTP223 을 아직 안 달았으면 보드의 PA27 버튼을 누르면 터치로 친다.
 *     ⚠️ 시리얼은 pyserial 을 dtr=False·rts=False 로 열어야 로그가 보인다 (수신호 프로젝트 교훈)
 *   둘 다 OLED VCC → 3V3, GND → GND
 *
 * ★ 시리얼 (115200) 에 'u' 를 보내면 버튼 없이 굽기 모드로 들어간다 (NU40 = NRF52BOOT, NU87 = UART 다운로드).
 *   NU87 은 굽고 나서 RTS 를 한 번 토글하면 리셋된다 (Tiny DK 는 RTS→RESET 은 있고 BOOT 자동 회로는 없음).
 *   ⚠️ 모든 Serial 출력은 if (Serial) 로 감싼다 — 안 그러면 충전기에 꽂았을 때 멈춘다 (스타보이 교훈).
 *
 * 그리기는 Adafruit GFX 에 없는 fillArc 만 직접 만든다 (화면이 128×64 라 픽셀을 훑어도 빠르다).
 */

#if defined(NRF52840_XXAA)
  #define BOARD_NU40 1
  #include <Adafruit_TinyUSB.h>   // 없으면 Serial 이 링크되지 않는다
#endif
#ifndef BOARD_NU40
extern "C" {
  #include "ameba_soc.h"   // BKUP_Set, BIT_UARTBURN_BOOT — 'u' 로 굽기 모드 들어갈 때
  void sys_reset(void);
}
#endif
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ─────────────── 핀 ───────────────
#ifdef BOARD_NU40
static const int PIN_TOUCH = 28;   // P0.28 — TTP223 OUT (가안. 다른 핀에 꽂았으면 여기만 바꾸기)
static const int PIN_S1 = 11;      // P0.11 — 보드 S1 버튼 (누르면 LOW)
#else
static const int PIN_TOUCH = PA28; // NU87 — TTP223 OUT (가안)
static const int PIN_S1 = PA27;    // NU87 Tiny DK 보드의 PA27 버튼 (누르면 LOW) — TTP223 달기 전 터치 대용
#endif

// ─────────────── 화면 ───────────────
static const int W = 128, H = 64;
Adafruit_SSD1306 display(W, H, &Wire, -1);
bool displayOk = false;

// ─────────────── 튜닝 값 (시뮬레이터 PET_CFG 와 같게) ───────────────
static const uint32_t SLEEP_MS = 4000;       // 이벤트 끝나고 이만큼 지나면 다시 잠 (평소엔 잠)
static const uint32_t HAPPY_MS = 1800;
static const uint32_t WAKING_MS = 1300;
static const float BLINK_MIN = 2200, BLINK_MAX = 5200, BLINK_LEN = 160;
static const float WANDER_MIN = 1200, WANDER_MAX = 3200;
static const float GAZE_EASE = 0.008f;       // ms 당
static const float S = 0.66f;                // 얼굴 크기 배율 (OLED 홈 화면과 같음)

// ─────────────── 상태 ───────────────
enum State { IDLE, HAPPY, ASLEEP, WAKING, NOTIFY, PICTURE };
struct Pet {
  State state = ASLEEP;       // 켜자마자 잠
  uint32_t stateMs = 0;
  uint32_t idleMs = 0;        // 마지막 터치 뒤 지난 시간
  float blinkIn = 3000, blinkT = -1;
  float wanderIn = 0, wx = 0, wy = 0;
  float gx = 0, gy = 0;       // 시선 -1~1
  float t = 0;                // 초
  char notif = 0;             // 지금 보여주는 알림 'k' / 'g'
  bool unreadK = false, unreadG = false;   // 구석에 남는 표시
  uint32_t unreadMs = 0;      // 마지막 알림 뒤 지난 시간
  uint32_t happyMs = HAPPY_MS;
} pet;
static const uint32_t NOTIFY_MS = 5000;
uint8_t nameBmp[256];         // 보낸 사람 이름 그림 128×16
bool hasName = false;
uint8_t wideBmp[512];         // 긴 이름 256×16 (옆으로 흐름)
bool nameWide = false;
int nameW = 0;                // 긴 이름의 실제 글자 폭 (px)
uint32_t notifyMs = 5000;
uint8_t picBmp[1024];         // 맥이 보낸 화면 한 장 128×64
static const uint32_t PICTURE_MS = 8000;
static const uint32_t UNREAD_MS = 5UL * 60 * 1000;   // 구석 아이콘 유지 시간

void setState(State s) { pet.state = s; pet.stateMs = 0; }

float frand(float lo, float hi) { return lo + (hi - lo) * (random(10000) / 10000.0f); }

// ─────────────── 그리기 도우미 ───────────────
// 도넛 조각: 안쪽 r0, 바깥 r1, 각도 a0~a1 (도, 0=오른쪽, 시계방향) — 시뮬레이터 g.fillArc 와 같은 규약
void fillArc(int cx, int cy, int r0, int r1, float a0, float a1) {
  for (int y = cy - r1; y <= cy + r1; y++) {
    if (y < 0 || y >= H) continue;
    for (int x = cx - r1; x <= cx + r1; x++) {
      if (x < 0 || x >= W) continue;
      int dx = x - cx, dy = y - cy, d2 = dx * dx + dy * dy;
      if (d2 > r1 * r1 || d2 < r0 * r0) continue;
      float a = atan2f((float)dy, (float)dx) * 57.2958f;
      if (a < 0) a += 360;
      if ((a >= a0 && a <= a1) || (a + 360 >= a0 && a + 360 <= a1)) display.drawPixel(x, y, SSD1306_WHITE);
    }
  }
}

// 굵은 선 (가로 짧은 선만 쓰므로 사각형으로 충분)
void hbar(int x0, int x1, int y, int t) { display.fillRect(x0, y - t / 2, x1 - x0 + 1, t, SSD1306_WHITE); }

// 도트 그림: 문자열 한 줄 = 픽셀 한 줄
void pix(const char *const *rows, int n, int x, int y) {
  for (int r = 0; r < n; r++)
    for (int k = 0; rows[r][k]; k++)
      if (rows[r][k] == '#') display.drawPixel(x + k, y + r, SSD1306_WHITE);
}
const char *const ZZZ[] = { "###", "..#", ".#.", "#..", "###" };
// 카톡 말풍선 (11×9) / 메일 봉투 (11×8)
const char *const TALK[] = {
  "..#######..", ".#########.", "###########", "###########", "###########",
  ".#########.", "..#######..", "..##.......", ".#........." };
const char *const MAIL[] = {
  "###########", "##.......##", "#.#.....#.#", "#..#...#..#", "#...#.#...#",
  "#....#....#", "#.........#", "###########" };
// 크게 (2배) 그리기
void pix2(const char *const *rows, int n, int x, int y) {
  for (int r = 0; r < n; r++)
    for (int k = 0; rows[r][k]; k++)
      if (rows[r][k] == '#') display.fillRect(x + k * 2, y + r * 2, 2, 2, SSD1306_WHITE);
}

// ─────────────── 버디 얼굴 (core/styles.js buddyEye / buddyMouth 를 옮긴 것) ───────────────
void drawEye(int x, int y, float open, State st) {
  if (st == HAPPY) {                         // ^ 눈
    fillArc(x, y + lroundf(6 * S), lroundf(7 * S), lroundf(14 * S), 200, 340);
    return;
  }
  if (st == NOTIFY) {                        // 놀란 눈 = 동그랗게
    display.fillCircle(x, y, lroundf(13 * S), SSD1306_WHITE);
    display.fillCircle(x, y, lroundf(5 * S), SSD1306_BLACK);
    return;
  }
  if (st == ASLEEP) {                        // 감은 눈 ∪
    fillArc(x, y - lroundf(4 * S), lroundf(9 * S), lroundf(13 * S), 25, 155);
    return;
  }
  int w = lroundf(26 * S), hFull = lroundf(32 * S), r = max(2L, lroundf(8 * S));
  int h = max(lroundf(4 * S), lroundf(hFull * open));
  display.fillRoundRect(x - w / 2, y - h / 2, w, h, min(r, h / 2), SSD1306_WHITE);
}

void drawMouth(int x, int y, State st, float t) {
  int a = lroundf(6 * S), b = lroundf(9.5f * S);
  if (st == HAPPY) {                         // 벌린 입 (D 모양)
    int cy = y - lroundf(2 * S);
    display.fillCircle(x, cy, b, SSD1306_WHITE);
    display.fillRect(x - b - 1, cy - b - 1, b * 2 + 2, b + 1, SSD1306_BLACK);
  } else if (st == WAKING || st == NOTIFY) { // o 입
    display.drawCircle(x, y, 3, SSD1306_WHITE);
  } else if (st == ASLEEP) {                 // 작은 일자
    hbar(x - 3, x + 3, y - 2, 2);
  } else {                                   // 기본 = 작은 대칭 미소
    fillArc(x, y - a, a, b, 35, 145);
  }
}

void drawFace() {
  float t = pet.t;
  float bob = 0;
  if (pet.state == HAPPY) bob = -fabsf(sinf(t * 8)) * 4;
  else if (pet.state == ASLEEP) bob = sinf(t * 0.8f) * 1.5f;   // 잠: 아주 느리게 숨쉬기 (업무 방해 안 되게)

  // 깜빡임 — 뜬 눈일 때만
  float open = 1;
  if (pet.blinkT >= 0) {
    float p = pet.blinkT / BLINK_LEN;
    open = p < 0.5f ? 1 - p * 2 : (p - 0.5f) * 2;
  }
  if (pet.state == WAKING || pet.state == NOTIFY) open = 1;

  const bool nameRow = pet.state == NOTIFY && hasName;
  const int cx = pet.state == NOTIFY ? 48 : 64, cy = nameRow ? 22 : 31;   // 알림 땐 얼굴을 왼쪽으로, 오른쪽에 아이콘, 이름 있으면 위로
  float ox = pet.gx * 14 * S, oy = pet.gy * 10 * S + bob * S;
  int eyeY = lroundf(cy - 12 * S + oy);
  float gap = 32 * S;
  drawEye(lroundf(cx - gap + ox), eyeY, open, pet.state);
  drawEye(lroundf(cx + gap + ox), eyeY, open, pet.state);
  drawMouth(lroundf(cx + ox), lroundf(cy + 26 * S + oy - 2 * S), pet.state, t);

  if (pet.state == ASLEEP) {                 // z 가 오른쪽 위로 떠오름
    float p = fmodf(t * 0.25f, 1.0f);
    pix(ZZZ, 5, cx + 36 + p * 6, cy - 16 - p * 8);
    if (p > 0.4f) pix(ZZZ, 5, cx + 44 + p * 4, cy - 24 - p * 6);
  }
  if (pet.state == NOTIFY) {                 // 아이콘이 통통 + 느낌표
    int by = (nameRow ? 12 : 18) - lroundf(fabsf(sinf(t * 7)) * 6);
    if (pet.notif == 'k') pix2(TALK, 9, 98, by); else pix2(MAIL, 8, 98, by);
    display.fillRect(122, by - 10, 3, 7, SSD1306_WHITE); display.fillRect(122, by - 1, 3, 2, SSD1306_WHITE);
    if (nameRow) {
      if (nameWide) {                        // 0.7초 멈춤 → 초당 30px 로 끝까지 → 멈춤
        int travel = max(0, nameW - 124);
        int off = constrain(((int)pet.stateMs - 700) * 30 / 1000, 0, travel);
        display.drawBitmap(-off, 48, wideBmp, 256, 16, SSD1306_WHITE);
      } else {
        display.drawBitmap(0, 48, nameBmp, 128, 16, SSD1306_WHITE);
      }
    } else {
      display.setTextSize(1); display.setTextColor(SSD1306_WHITE);
      display.setCursor(102, by + 22); display.print(pet.notif == 'k' ? "TALK" : "MAIL");
    }
  } else {                                   // 평소: 안 읽은 알림 작은 아이콘 (오른쪽 위 구석)
    int x = 116;
    if (pet.unreadK) { pix(TALK, 9, x, 1); x -= 13; }
    if (pet.unreadG) pix(MAIL, 8, x, 1);
  }
  if (pet.state == WAKING) {                 // ? 표시
    display.setTextSize(1); display.setTextColor(SSD1306_WHITE);
    display.setCursor(cx + 36, cy - 20); display.print('?');
  }
}

// ─────────────── 입력 ───────────────
bool touchedEdge() {
  static bool was = false;
  bool now = digitalRead(PIN_TOUCH) == HIGH || (PIN_S1 >= 0 && digitalRead(PIN_S1) == LOW);
  bool edge = now && !was;
  was = now;
  return edge;
}

void onNotify(char k) {
  pet.idleMs = 0;
  pet.notif = k;
  pet.unreadMs = 0;
  if (k == 'k') pet.unreadK = true; else pet.unreadG = true;
  setState(NOTIFY);
  if (Serial) Serial.println(k == 'k' ? "알림: 카톡" : "알림: 지메일");
}

void onTouch() {
  pet.idleMs = 0;
  pet.unreadK = pet.unreadG = false;
  pet.happyMs = HAPPY_MS;
  if (pet.state == ASLEEP) setState(WAKING);
  else setState(HAPPY);
  if (Serial) Serial.println("터치");
}

// 'n' 뒤의 이름 그림 받기 (그림 바이트에 'u' 같은 글자가 섞여도 명령으로 안 보게)
int rxName = -1;              // -1 = 평소, 0 = 종류 기다림, 1~256 = 그림 받는 중
int rxWide = -1;              // 'N': -1 = 평소, 0 = 종류, 1~2 = 폭, 3~514 = 그림
int rxPic = -1;               // -1 = 평소, 0~1023 = 화면 받는 중
char rxKind = 0;
uint32_t rxMs = 0;

void pollSerial() {
  if (!Serial) return;
  if ((rxName >= 0 || rxPic >= 0 || rxWide >= 0) && millis() - rxMs > 1000) rxName = rxPic = rxWide = -1;   // 중간에 끊기면 버림
  while (Serial.available()) {
    char c = Serial.read();
    if (rxWide >= 0) {
      uint8_t b = (uint8_t)c; rxMs = millis();
      if (rxWide == 0) rxKind = c;
      else if (rxWide == 1) nameW = b;
      else if (rxWide == 2) nameW |= b << 8;
      else wideBmp[rxWide - 3] = b;
      if (++rxWide > 514) {
        rxWide = -1; hasName = true; nameWide = true;
        notifyMs = 1400 + max(0, nameW - 124) * 1000 / 30 + 2000;   // 다 흘러간 뒤 2초 더
        onNotify(rxKind);
      }
      continue;
    }
    if (rxPic >= 0) {
      picBmp[rxPic++] = (uint8_t)c; rxMs = millis();
      if (rxPic >= 1024) { rxPic = -1; pet.idleMs = 0; setState(PICTURE); if (Serial) Serial.println("화면 받음"); }
      continue;
    }
    if (rxName == 0) { rxKind = c; rxName = 1; rxMs = millis(); continue; }
    if (rxName > 0) {
      nameBmp[rxName - 1] = (uint8_t)c;
      if (++rxName > 256) { rxName = -1; hasName = true; nameWide = false; notifyMs = NOTIFY_MS; onNotify(rxKind); }
      continue;
    }
    if (c == 'n') { rxName = 0; rxMs = millis(); continue; }
    if (c == 'N') { rxWide = 0; rxMs = millis(); continue; }
    if (c == 'p') { rxPic = 0; rxMs = millis(); continue; }
#ifdef BOARD_NU40
    if (c == 'u') {                          // 굽기 모드로 (리셋 버튼 없이)
      Serial.println("DFU 로 들어감");
      delay(50);
      NRF_POWER->GPREGRET = 0x57;
      NVIC_SystemReset();
    }
#else
    if (c == 'u') {                          // NU87: BOOT 버튼 없이 UART 굽기 모드로 다시 켜짐 (Tiny DK 는 BOOT 자동 회로가 없다)
      Serial.println("UART 굽기 모드로 들어감");
      delay(50);
      BKUP_Set(0, BIT_UARTBURN_BOOT);
      sys_reset();
    }
#endif
    if (c == 't') onTouch();                 // 시리얼로 터치 흉내 (배선 전 확인용)
    if (c == 'K') pet.unreadK = false;       // 맥에서 카톡 창을 봤음 → 말풍선 표시만 조용히 지움
    if (c == 'G') pet.unreadG = false;       // 지메일 탭을 봤음 → 봉투 표시만 지움
    if (c == 'k' || c == 'g') { hasName = false; notifyMs = NOTIFY_MS; onNotify(c); }   // 이름 없이 알림
    if (c == 'h') { pet.idleMs = 0; pet.happyMs = 4000; setState(HAPPY); Serial.println("좋아함 (Claude 끝)"); }
  }
}

// ─────────────── setup / loop ───────────────
void setup() {
  Serial.begin(115200);
  pinMode(PIN_TOUCH, INPUT_PULLDOWN);        // TTP223 은 닿으면 HIGH. 안 꽂혀 있어도 LOW 로 가만히
  if (PIN_S1 >= 0) pinMode(PIN_S1, INPUT_PULLUP);
  randomSeed(20261026);

  if (Serial) Serial.println("[desk_pet] 시작");
  Wire.begin();
  Wire.setClock(400000);
  // 마지막 false = 라이브러리가 Wire.begin() 을 또 부르지 않게.
  // ⚠️ NU87(Ameba) 은 Wire.begin() 을 두 번 부르면 "Incorrect pin: 26" 이 나고 I2C 가 깨진다 (2026-10-26 실물)
  displayOk = display.begin(SSD1306_SWITCHCAPVCC, 0x3C, true, false);
  if (!displayOk) displayOk = display.begin(SSD1306_SWITCHCAPVCC, 0x3D, true, false);
  if (displayOk) { display.clearDisplay(); display.display(); }
  if (Serial) Serial.println(displayOk ? "[breadpet] OLED 찾음" : "[breadpet] OLED 없음 (선 확인) — 얼굴은 안 보이고 터치·시리얼만 돈다");
}

void loop() {
  static uint32_t last = millis();
  uint32_t now = millis();
  uint32_t dt = now - last;
  if (dt < 33) { pollSerial(); return; }     // 약 30fps
  if (dt > 100) dt = 100;
  last = now;

  pollSerial();
  if (touchedEdge()) onTouch();

  pet.t += dt / 1000.0f;
  pet.stateMs += dt;
  pet.idleMs += dt;
  pet.unreadMs += dt;
  if (pet.unreadMs >= UNREAD_MS) pet.unreadK = pet.unreadG = false;

  // 상태 전이
  if (pet.state == HAPPY && pet.stateMs >= pet.happyMs) setState(IDLE);
  if (pet.state == WAKING && pet.stateMs >= WAKING_MS) setState(IDLE);
  if (pet.state == NOTIFY && pet.stateMs >= notifyMs) setState(IDLE);
  if (pet.state == PICTURE && pet.stateMs >= PICTURE_MS) setState(IDLE);
  if (pet.state == IDLE && pet.idleMs >= SLEEP_MS) setState(ASLEEP);

  // 깜빡임
  pet.blinkIn -= dt;
  if (pet.blinkIn <= 0 && pet.blinkT < 0) { pet.blinkT = 0; pet.blinkIn = frand(BLINK_MIN, BLINK_MAX); }
  if (pet.blinkT >= 0) { pet.blinkT += dt; if (pet.blinkT >= BLINK_LEN) pet.blinkT = -1; }

  // 두리번 (기본일 때만), 나머지는 정면
  pet.wanderIn -= dt;
  if (pet.wanderIn <= 0) {
    pet.wanderIn = frand(WANDER_MIN, WANDER_MAX);
    pet.wx = frand(-0.8f, 0.8f); pet.wy = frand(-0.5f, 0.4f);
  }
  float tx = pet.state == IDLE ? pet.wx : 0, ty = pet.state == IDLE ? pet.wy : 0;
  float k = min(1.0f, GAZE_EASE * dt);
  pet.gx += (tx - pet.gx) * k;
  pet.gy += (ty - pet.gy) * k;

  if (!displayOk) return;
  display.clearDisplay();
  if (pet.state == PICTURE) { display.drawBitmap(0, 0, picBmp, 128, 64, SSD1306_WHITE); display.display(); return; }
  drawFace();
  display.display();
}
