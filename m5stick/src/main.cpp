// AI Usage Bar — M5StickC Plus firmware (USB Serial edition)
//
// Reads newline-terminated JSON lines from USB Serial @115200 baud.
// The Mac widget pushes the latest snapshot every few seconds.
//
// Buttons:
//   A (front, "M5"): toggle 5h ↔ 7d view
//   B (side):        flip display rotation (left/right hand)
//
// No WiFi, no network — works as long as USB cable is plugged in.

#include <Arduino.h>
#include <M5StickCPlus.h>
#include <ArduinoJson.h>

// ============ Display dimensions (set in setup() from M5.Lcd) ============
static int W = 240;
static int H = 135;

#define COL_BG       TFT_BLACK
#define COL_FG       TFT_WHITE
#define COL_DIM      0x8410
#define COL_TRACK    0x4208
#define COL_GREEN    0x0648
#define COL_YELLOW   0xFEE0
#define COL_ORANGE   0xFC60
#define COL_RED      0xF1E0
#define COL_CLAUDE   0xFC00
#define COL_GPT      0xFFFF

// ============ App state ============
struct ProviderUsage {
    bool   available  = false;
    float  fivePct    = 0;
    float  sevenPct   = 0;
    long   fiveLeft   = 0;   // seconds remaining
    long   sevenLeft  = 0;
};

ProviderUsage claudeData;
ProviderUsage codexData;

bool showSevenDay = false;
bool everReceived = false;
unsigned long lastReceived = 0;
String lastError;

uint8_t rotation = 0;             // 0 = 竖屏 (USB 在下), 2 = 竖屏倒过来

// 串口接收缓冲
String rxBuf;

// ============ Utility ============
uint16_t pickColor(float pct) {
    if (pct < 50)  return COL_GREEN;
    if (pct < 75)  return COL_YELLOW;
    if (pct < 90)  return COL_ORANGE;
    return COL_RED;
}

void drawProgressBar(int x, int y, int w, int h, float pct, uint16_t fg) {
    if (pct < 0) pct = 0;
    if (pct > 100) pct = 100;
    int filled = (int)(w * pct / 100.0f);
    M5.Lcd.fillRoundRect(x, y, w, h, 2, COL_TRACK);
    if (filled > 0) M5.Lcd.fillRoundRect(x, y, filled, h, 2, fg);
    M5.Lcd.drawRoundRect(x, y, w, h, 2, COL_DIM);
}

String fmtCountdown(long sec) {
    if (sec <= 0) return "now";
    if (sec >= 86400) {
        long d = sec / 86400;
        long h = (sec % 86400) / 3600;
        if (h == 0) return String(d) + "d";
        return String(d) + "d " + String(h) + "h";
    }
    long h = sec / 3600;
    long m = (sec % 3600) / 60;
    if (h > 0) return String(h) + "h " + String(m) + "m";
    return String(m) + "m";
}

// ============ ISO timestamp helper ============
// Returns (resets_at_epoch - now_epoch) in seconds. Both inputs are ISO 8601
// UTC ("YYYY-MM-DDTHH:MM:SS..."). We treat them as UTC tm structs and diff.
long isoDeltaSeconds(const char* iso, const char* nowIso) {
    if (!iso || !*iso || !nowIso || !*nowIso) return 0;
    auto parse = [](const char* s) -> long {
        int Y, M, D, h, m, sec;
        if (sscanf(s, "%4d-%2d-%2dT%2d:%2d:%2d", &Y, &M, &D, &h, &m, &sec) != 6) return 0;
        struct tm t = {};
        t.tm_year = Y - 1900; t.tm_mon = M - 1; t.tm_mday = D;
        t.tm_hour = h; t.tm_min = m; t.tm_sec = sec;
        return (long)mktime(&t);
    };
    long a = parse(iso);
    long b = parse(nowIso);
    if (!a || !b) return 0;
    return a - b;
}

// ============ Render ============
//
// 竖屏布局 (135×240, portrait):
//   Header           y=0..14    高 14
//   Claude block     y=20..108  高 88
//     label          y=20..36   size 2 = 16 高
//     big %          y=44..76   size 4 = 32 高
//     progress bar   y=84..94   高 10
//     reset text     y=100..108 size 1 = 8 高
//   Divider          y=114
//   GPT block        y=120..208 (同 Claude)
//   Footer           y=216..230 size 1

static const int ROW_H        = 88;
static const int CLAUDE_Y     = 20;
static const int GPT_Y        = 120;
static const int FOOTER_Y     = 216;

void renderProvider(int y, const char* label, uint16_t labelColor,
                    const ProviderUsage& d, bool showSeven) {
    // 先整块清空，避免文字残留
    M5.Lcd.fillRect(0, y, W, ROW_H, COL_BG);

    // 标签 (size 2, 高 16)
    M5.Lcd.setTextSize(2);
    M5.Lcd.setTextColor(labelColor, COL_BG);
    M5.Lcd.setCursor(8, y);
    M5.Lcd.print(label);

    if (!d.available) {
        M5.Lcd.setTextColor(COL_RED, COL_BG);
        M5.Lcd.setCursor(8, y + 40);
        M5.Lcd.print("offline");
        return;
    }

    float pct = showSeven ? d.sevenPct : d.fivePct;
    long left = showSeven ? d.sevenLeft : d.fiveLeft;

    // 大字号百分比 (size 4 = 24×32)
    char buf[16];
    snprintf(buf, sizeof(buf), "%d%%", (int)pct);
    M5.Lcd.setTextSize(4);
    M5.Lcd.setTextColor(COL_FG, COL_BG);
    // 计算文本宽度居中
    int textW = strlen(buf) * 24;
    int cx = (W - textW) / 2;
    if (cx < 4) cx = 4;
    M5.Lcd.setCursor(cx, y + 24);
    M5.Lcd.print(buf);

    // 进度条 (高 10, 居中)
    int barW = W - 16;
    drawProgressBar(8, y + 64, barW, 10, pct, pickColor(pct));

    // 倒计时 (size 1, 居中)
    M5.Lcd.setTextSize(1);
    M5.Lcd.setTextColor(COL_DIM, COL_BG);
    String rs = String("resets in ") + fmtCountdown(left);
    int rTextW = rs.length() * 6;
    int rx = (W - rTextW) / 2;
    if (rx < 4) rx = 4;
    M5.Lcd.setCursor(rx, y + 80);
    M5.Lcd.print(rs);
}

void renderHeader() {
    M5.Lcd.fillRect(0, 0, W, 14, COL_BG);
    M5.Lcd.setTextSize(1);
    M5.Lcd.setTextColor(COL_DIM, COL_BG);
    M5.Lcd.setCursor(6, 3);
    M5.Lcd.print(showSevenDay ? "7-day window" : "5h window");

    // 接收状态点
    uint16_t statusColor = everReceived
        ? (millis() - lastReceived < 15000 ? COL_GREEN : COL_YELLOW)
        : COL_RED;
    M5.Lcd.fillRect(W - 10, 4, 6, 6, statusColor);
}

void renderDivider(int y) {
    M5.Lcd.fillRect(8, y, W - 16, 1, COL_TRACK);
}

void renderFooter() {
    M5.Lcd.fillRect(0, FOOTER_Y, W, 14, COL_BG);
    M5.Lcd.setTextSize(1);
    M5.Lcd.setCursor(6, FOOTER_Y + 3);
    if (!everReceived) {
        M5.Lcd.setTextColor(COL_DIM, COL_BG);
        M5.Lcd.print("waiting for data");
    } else if (lastError.length() > 0) {
        M5.Lcd.setTextColor(COL_RED, COL_BG);
        M5.Lcd.print(lastError);
    } else {
        M5.Lcd.setTextColor(COL_DIM, COL_BG);
        long age = (long)((millis() - lastReceived) / 1000);
        char buf[24];
        snprintf(buf, sizeof(buf), "updated %lds ago", age);
        M5.Lcd.print(buf);
    }
}

void render() {
    renderHeader();
    renderProvider(CLAUDE_Y, "Claude", COL_CLAUDE, claudeData, showSevenDay);
    renderDivider(114);
    renderProvider(GPT_Y,    "GPT",    COL_GPT,    codexData,  showSevenDay);
    renderFooter();
}

// ============ Parse a JSON line ============
void handleLine(const String& line) {
    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, line);
    if (err) {
        lastError = String("JSON: ") + err.c_str();
        return;
    }

    const char* nowIso = doc["ts"] | "";

    auto fillFrom = [&](JsonObject src, ProviderUsage& dst) {
        if (src.isNull()) {
            dst.available = false;
            return;
        }
        dst.available = src["available"] | false;
        if (!dst.available) return;
        dst.fivePct  = src["five_hour_pct"] | 0.0f;
        dst.sevenPct = src["seven_day_pct"] | 0.0f;
        const char* r5 = src["five_hour_resets_at"] | "";
        const char* r7 = src["seven_day_resets_at"] | "";
        dst.fiveLeft  = isoDeltaSeconds(r5, nowIso);
        dst.sevenLeft = isoDeltaSeconds(r7, nowIso);
    };

    fillFrom(doc["claude"].as<JsonObject>(), claudeData);
    fillFrom(doc["codex"].as<JsonObject>(),  codexData);

    lastError = "";
    everReceived = true;
    lastReceived = millis();
    render();
}

// ============ Setup / Loop ============
void setup() {
    M5.begin();
    // 强制横屏，并从 lib 读回真实尺寸（避免硬编码错位）
    M5.Lcd.setRotation(rotation);
    W = M5.Lcd.width();
    H = M5.Lcd.height();

    M5.Lcd.fillScreen(COL_BG);
    M5.Axp.ScreenBreath(15);

    Serial.begin(115200);
    Serial.printf("AI Usage Bar — USB Serial mode  |  LCD %dx%d (rot=%d)\n",
                  W, H, rotation);

    // 启动占位
    M5.Lcd.setTextColor(COL_FG);
    M5.Lcd.setTextSize(2);
    M5.Lcd.setCursor(20, 30);
    M5.Lcd.print("AI USAGE");
    M5.Lcd.setTextSize(1);
    M5.Lcd.setTextColor(COL_DIM);
    M5.Lcd.setCursor(20, 60);
    M5.Lcd.print("Waiting for USB data from");
    M5.Lcd.setCursor(20, 72);
    M5.Lcd.print("the Mac widget...");

    rxBuf.reserve(2048);
}

void loop() {
    M5.update();

    // 串口读到换行就解析
    while (Serial.available() > 0) {
        char c = (char)Serial.read();
        if (c == '\n') {
            if (rxBuf.length() > 0) {
                handleLine(rxBuf);
                rxBuf = "";
            }
        } else if (c != '\r') {
            rxBuf += c;
            if (rxBuf.length() > 4096) rxBuf = "";   // 防爆缓冲
        }
    }

    // 按键 A：切 5h / 7d
    if (M5.BtnA.wasPressed()) {
        showSevenDay = !showSevenDay;
        render();
    }
    // 按键 B：180 度翻转屏幕（适配上下颠倒摆放）
    if (M5.BtnB.wasPressed()) {
        rotation = (rotation == 0) ? 2 : 0;
        M5.Lcd.setRotation(rotation);
        W = M5.Lcd.width();
        H = M5.Lcd.height();
        M5.Lcd.fillScreen(COL_BG);
        render();
    }

    // 周期性更新倒计时（每秒刷一次屏，让 "1h 28m" 跟着时间走）
    static unsigned long lastTick = 0;
    if (millis() - lastTick > 1000) {
        if (everReceived) {
            // 自然时间流逝：把剩余秒数 -1
            if (claudeData.fiveLeft > 0)  claudeData.fiveLeft--;
            if (claudeData.sevenLeft > 0) claudeData.sevenLeft--;
            if (codexData.fiveLeft > 0)   codexData.fiveLeft--;
            if (codexData.sevenLeft > 0)  codexData.sevenLeft--;
            render();
        }
        lastTick = millis();
    }

    delay(20);
}
