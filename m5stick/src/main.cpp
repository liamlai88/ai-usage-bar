// AI Usage Bar — M5StickC Plus firmware
//
// Connects to your WiFi, polls the Mac widget's HTTP server every 30s,
// and renders 5h / 7d usage with color-coded progress bars on the LCD.
//
// Buttons:
//   A (front, "M5"): toggle view (5h ↔ 7d)
//   B (side):        force refresh
//
// Build: place secrets.h in include/, then `pio run -t upload`.

#include <Arduino.h>
#include <M5StickCPlus.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "secrets.h"

// ============ Display constants (landscape 240×135) ============
static const uint16_t W = 240;
static const uint16_t H = 135;

// 565 colors
#define COL_BG       TFT_BLACK
#define COL_FG       TFT_WHITE
#define COL_DIM      0x8410  // gray
#define COL_TRACK    0x4208  // dark gray
#define COL_GREEN    0x0648
#define COL_YELLOW   0xFEE0
#define COL_ORANGE   0xFC60
#define COL_RED      0xF1E0
#define COL_CLAUDE   0xFC00  // anthropic orange
#define COL_GPT      0xFFFF

// ============ App state ============
struct ProviderUsage {
    bool   available  = false;
    float  fivePct    = 0;
    float  sevenPct   = 0;
    long   fiveReset  = 0;  // epoch seconds
    long   sevenReset = 0;
    String error;
};

ProviderUsage claudeData;
ProviderUsage codexData;

unsigned long lastFetch    = 0;
unsigned long lastRender   = 0;
const uint32_t FETCH_EVERY = 30 * 1000;
const uint32_t RENDER_EVERY = 1000;  // 用于刷新倒计时

bool showSevenDay = false;  // false = 5h, true = 7d
bool wifiConnected = false;
String lastError;

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
    // 轨道
    M5.Lcd.fillRoundRect(x, y, w, h, 2, COL_TRACK);
    // 填充
    if (filled > 0) {
        M5.Lcd.fillRoundRect(x, y, filled, h, 2, fg);
    }
    // 边框
    M5.Lcd.drawRoundRect(x, y, w, h, 2, COL_DIM);
}

String fmtCountdown(long resetEpoch) {
    if (resetEpoch == 0) return "-";
    long now = (long)(millis() / 1000) + lastFetch / 1000;
    // 我们没维护真实 UTC 时钟，只用相对值近似
    // 后端给的是绝对时间戳，前端拿到时也算近似
    // 这里简化：用 (resetEpoch - fetchedAtEpoch) 当作"剩余秒数"
    long sec = resetEpoch;
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

// ============ Parse ISO 8601 to epoch (rough) ============
// 我们只需要知道"距现在还剩多少秒"，所以请求时记录 fetch 时间，
// 用 resets_at - fetched_at 算出剩余秒数。
long isoDeltaSeconds(const char* iso, const char* nowIso) {
    if (!iso || !nowIso) return 0;
    // 解析 YYYY-MM-DDTHH:MM:SS（粗略，忽略小数和 TZ）
    auto parse = [](const char* s) -> long {
        struct tm t = {};
        int Y, M, D, h, m, sec;
        if (sscanf(s, "%4d-%2d-%2dT%2d:%2d:%2d", &Y, &M, &D, &h, &m, &sec) != 6) {
            return 0;
        }
        t.tm_year = Y - 1900; t.tm_mon = M - 1; t.tm_mday = D;
        t.tm_hour = h; t.tm_min = m; t.tm_sec = sec;
        return (long)mktime(&t);
    };
    long ts = parse(iso);
    long now = parse(nowIso);
    if (ts == 0 || now == 0) return 0;
    return ts - now;
}

// ============ Fetch ============
bool fetchUsage() {
    if (!wifiConnected) return false;

    HTTPClient http;
    String url = String("http://") + USAGE_HOST + ":" + String(USAGE_PORT) + USAGE_PATH;
    http.begin(url);
    http.setTimeout(5000);

    int code = http.GET();
    if (code != 200) {
        lastError = "HTTP " + String(code);
        http.end();
        return false;
    }

    String body = http.getString();
    http.end();

    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, body);
    if (err) {
        lastError = String("JSON: ") + err.c_str();
        return false;
    }

    const char* nowIso = doc["ts"] | "";

    auto fillFrom = [&](JsonObject src, ProviderUsage& dst) {
        dst.available = src["available"] | false;
        if (!dst.available) {
            const char* e = src["error"] | "";
            dst.error = String(e);
            return;
        }
        dst.fivePct  = src["five_hour_pct"] | 0.0f;
        dst.sevenPct = src["seven_day_pct"] | 0.0f;
        const char* r5 = src["five_hour_resets_at"] | "";
        const char* r7 = src["seven_day_resets_at"] | "";
        dst.fiveReset  = isoDeltaSeconds(r5, nowIso);
        dst.sevenReset = isoDeltaSeconds(r7, nowIso);
        dst.error = "";
    };

    if (doc["claude"].is<JsonObject>()) fillFrom(doc["claude"], claudeData);
    if (doc["codex"].is<JsonObject>())  fillFrom(doc["codex"],  codexData);

    lastError = "";
    return true;
}

// ============ WiFi ============
void connectWiFi() {
    M5.Lcd.fillScreen(COL_BG);
    M5.Lcd.setCursor(8, 50);
    M5.Lcd.setTextColor(COL_FG);
    M5.Lcd.setTextSize(2);
    M5.Lcd.print("Connecting WiFi...");

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start < 15000) {
        delay(300);
        M5.Lcd.print(".");
    }

    wifiConnected = (WiFi.status() == WL_CONNECTED);
    M5.Lcd.fillScreen(COL_BG);
    if (wifiConnected) {
        M5.Lcd.setCursor(8, 50);
        M5.Lcd.print("WiFi OK\n  ");
        M5.Lcd.print(WiFi.localIP());
        delay(800);
    } else {
        M5.Lcd.setCursor(8, 50);
        M5.Lcd.setTextColor(COL_RED);
        M5.Lcd.print("WiFi failed");
    }
}

// ============ Render ============
void renderProvider(int y, const char* label, uint16_t labelColor,
                    const ProviderUsage& d, bool showSeven) {
    M5.Lcd.setTextSize(2);

    // Label
    M5.Lcd.setTextColor(labelColor, COL_BG);
    M5.Lcd.setCursor(8, y);
    M5.Lcd.print(label);

    if (!d.available) {
        M5.Lcd.setTextColor(COL_RED, COL_BG);
        M5.Lcd.setCursor(110, y);
        M5.Lcd.print("offline");
        // 清掉旧进度条
        M5.Lcd.fillRect(8, y + 20, 224, 12, COL_BG);
        // 清掉重置时间
        M5.Lcd.fillRect(8, y + 36, 224, 14, COL_BG);
        return;
    }

    float pct  = showSeven ? d.sevenPct : d.fivePct;
    long reset = showSeven ? d.sevenReset : d.fiveReset;

    // 百分比文字（右对齐）
    char buf[16];
    snprintf(buf, sizeof(buf), "%3.0f%%", pct);
    M5.Lcd.setTextColor(COL_FG, COL_BG);
    // 估算宽度: 4 chars * 12px = 48px
    M5.Lcd.setCursor(W - 8 - 12 * 4, y);
    M5.Lcd.print(buf);

    // 进度条
    drawProgressBar(8, y + 20, 224, 10, pct, pickColor(pct));

    // 重置倒计时
    M5.Lcd.setTextSize(1);
    M5.Lcd.setTextColor(COL_DIM, COL_BG);
    M5.Lcd.setCursor(8, y + 34);
    M5.Lcd.print("resets in ");
    M5.Lcd.print(fmtCountdown(reset));
    // 清掉行尾旧字符
    int curX = M5.Lcd.getCursorX();
    if (curX < W) M5.Lcd.fillRect(curX, y + 34, W - curX, 10, COL_BG);
}

void render() {
    // 顶部标题
    M5.Lcd.fillRect(0, 0, W, 18, COL_BG);
    M5.Lcd.setTextSize(1);
    M5.Lcd.setTextColor(COL_DIM, COL_BG);
    M5.Lcd.setCursor(8, 5);
    M5.Lcd.print("AI USAGE");

    // 视图模式
    M5.Lcd.setCursor(W - 50, 5);
    M5.Lcd.print(showSevenDay ? "[7 days]" : "[5 hour]");

    // WiFi 状态
    M5.Lcd.fillRect(W - 8, 2, 6, 6, wifiConnected ? COL_GREEN : COL_RED);

    // 两个 provider
    renderProvider(28, "Claude", COL_CLAUDE, claudeData, showSevenDay);
    renderProvider(82, "GPT",    COL_GPT,    codexData,  showSevenDay);

    // 最后一行：错误信息（如有）
    M5.Lcd.fillRect(0, 124, W, 11, COL_BG);
    if (lastError.length() > 0) {
        M5.Lcd.setTextSize(1);
        M5.Lcd.setTextColor(COL_RED, COL_BG);
        M5.Lcd.setCursor(8, 126);
        M5.Lcd.print(lastError);
    }
}

// ============ Setup / Loop ============
void setup() {
    M5.begin();
    M5.Lcd.setRotation(1);            // 横屏 240x135
    M5.Lcd.fillScreen(COL_BG);
    M5.Axp.ScreenBreath(11);          // 亮度

    Serial.begin(115200);
    Serial.println("AI Usage Bar — M5StickC Plus");

    connectWiFi();

    // 第一次拉数据
    if (fetchUsage()) lastFetch = millis();
    render();
}

void loop() {
    M5.update();

    // 按键：A 切换 5h / 7d
    if (M5.BtnA.wasPressed()) {
        showSevenDay = !showSevenDay;
        render();
    }
    // 按键：B 强制刷新
    if (M5.BtnB.wasPressed()) {
        if (fetchUsage()) lastFetch = millis();
        render();
    }

    // 定时拉数据
    if (millis() - lastFetch > FETCH_EVERY) {
        if (fetchUsage()) lastFetch = millis();
        render();
    }

    // 重连 WiFi
    if (WiFi.status() != WL_CONNECTED && wifiConnected) {
        wifiConnected = false;
        render();
    } else if (WiFi.status() == WL_CONNECTED && !wifiConnected) {
        wifiConnected = true;
        render();
    }

    delay(50);
}
