import pygetwindow as gw
import pyautogui
import time
import sqlite3
import csv
import os
import sys
from collections import Counter
from google.cloud import vision
from google.oauth2 import service_account

# 🔧 請根據你的情境設定以下路徑和變數
GROUP_ICON = "group_test.png"
NOTEBOOK_ICON = "notebook_icon.png"
BUBBLE_ICON = "bubble_icon.png"
DB_NAME = "notes.db"
CSV_PATH = "notes.csv"
BASE_DIR = "screenshots"
credentials = service_account.Credentials.from_service_account_file("vision_key.json")


def switch_to_line():
    print("🔍 嘗試切換到 LINE 視窗...")
    try:
        win_list = [w for w in gw.getWindowsWithTitle('LINE') if not w.isMinimized]
        if not win_list:
            win_list = [w for w in gw.getWindowsWithTitle('LINE')]
        if not win_list:
            print("❌ 找不到 LINE 視窗，可能被關閉")
            return False

        win = win_list[0]
        win.restore()
        time.sleep(0.5)
        win.activate()
        time.sleep(0.5)
        pyautogui.click(win.left + 10, win.top + 10)
        print("✅ 使用 pygetwindow 成功切換至 LINE")
        return True
    except Exception as e:
        print("❌ 無法聚焦 LINE 視窗:", e)
        return False


def double_click_icon(icon_path, desc):
    print(f"💕 嘗試點擊：{desc}")
    pos = pyautogui.locateCenterOnScreen(icon_path, confidence=0.85)
    if pos:
        pyautogui.doubleClick(pos)
        time.sleep(1.5)
        return True
    else:
        print(f"❌ 找不到 {desc} 圖示：{icon_path}")
        return False


def capture_and_ocr_from_path(img_path):
    client = vision.ImageAnnotatorClient(credentials=credentials)
    with open(img_path, 'rb') as image_file:
        content = image_file.read()
        image = vision.Image(content=content)
    try:
        response = client.text_detection(image=image)
        texts = response.text_annotations
        if not texts:
            print("⚠️ 沒有偵測到任何文字")
            return [], []
        full_text = texts[0].description
        print("📋 OCR 結果如下：\n", full_text)
        lines = [line.strip() for line in full_text.splitlines() if line.strip()]
        plus_ones = extract_plus_one_messages(lines)
        return plus_ones, lines
    except Exception as e:
        print(f"❌ OCR 發生錯誤：{e}")
        return [], []


def extract_plus_one_messages(lines):
    plus_ones = []
    for i, line in enumerate(lines):
        if "+1" in line:
            plus_ones.append(lines[i - 1] if i > 0 else "未知")
    return plus_ones


def save_to_db_and_csv(messages):
    if not messages:
        return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT UNIQUE,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    for msg in messages:
        c.execute("INSERT OR IGNORE INTO notes (content) VALUES (?)", (msg,))
    conn.commit()
    conn.close()

    with open(CSV_PATH, 'a', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        for msg in messages:
            writer.writerow([msg])

    print(f"📂 已儲存資料到 DB 與 {CSV_PATH}，新增筆數：{len(messages)}")
    print(f"🧰 加總票數：{len(messages)}")
    counter = Counter([msg.split(":")[0].strip() for msg in messages if ":" in msg])
    print("\n📊 個別票數統計：")
    for name, count in counter.items():
        print(f"  - {name}: {count} 票")


def process_notebook_posts():
    if not switch_to_line(): sys.exit()
    if not double_click_icon(GROUP_ICON, "測試用群組圖示"): sys.exit()
    if not double_click_icon(NOTEBOOK_ICON, "記事本圖示"): sys.exit()

    print("📖 開始處理每一篇記事本...")
    all_bubbles = list(pyautogui.locateAllOnScreen(BUBBLE_ICON, confidence=0.85))
    if not all_bubbles:
        print("❌ 找不到任何記事本項目")
        return

    os.makedirs(BASE_DIR, exist_ok=True)

    for i, pos in enumerate(all_bubbles):
        print(f"\n🔽 正在展開第 {i+1} 篇記事本...")

        # 記錄點開前滑鼠位置
        prev_x, prev_y = pyautogui.position()

        pyautogui.click(pos)  # 展開本篇
        time.sleep(2)

        # 截圖
        screenshot_path = os.path.join(BASE_DIR, f'screenshot_{i+1}.png')
        image = pyautogui.screenshot()
        image.save(screenshot_path)
        print(f"📸 截圖已儲存至：{screenshot_path}")

        # OCR 處理
        plus_ones, _ = capture_and_ocr_from_path(screenshot_path)
        print("📊 +1 名單：", plus_ones)
        save_to_db_and_csv(plus_ones)

        # 👉 收回：回到原來滑鼠位置再點一下
        pyautogui.moveTo(prev_x, prev_y, duration=0.3)
        pyautogui.click()
        time.sleep(1.5)



def main():
    process_notebook_posts()


if __name__ == "__main__":
    main()
