import pytesseract
import pygetwindow as gw
import pyautogui
import sqlite3
import time
import sys
import os
import csv
from PIL import Image

# Tesseract 路徑設定
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 圖片資源與儲存路徑
BASE_DIR = r'C:\Users\chimou\Desktop\linebot 0608'
GROUP_ICON = os.path.join(BASE_DIR, 'group_test.PNG')
NOTEBOOK_ICON = os.path.join(BASE_DIR, 'notebook_icon.png')
BUBBLE_ICON = os.path.join(BASE_DIR, '0f777bdf-d7c1-4300-b07b-d1f72e7b4fb9.png')
SCREENSHOT_PATH = os.path.join(BASE_DIR, 'screenshot_debug.png')
CSV_PATH = os.path.join(BASE_DIR, 'output.csv')
DB_NAME = 'line_notes.db'

def switch_to_line():
    windows = gw.getWindowsWithTitle('LINE')
    if not windows:
        print("❌ 找不到 LINE 視窗，請確認 LINE 是否已開啟。")
        return False
    win = windows[0]
    if win.isMinimized:
        win.restore()
    win.activate()
    time.sleep(1)
    return True

def double_click_icon(icon_path, desc):
    print(f"🖱️ 嘗試點擊：{desc}")
    pos = pyautogui.locateCenterOnScreen(icon_path, confidence=0.85)
    if pos:
        pyautogui.doubleClick(pos)
        time.sleep(1.5)
        return True
    else:
        print(f"❌ 找不到 {desc} 圖示：{icon_path}")
        return False

def single_click_icon(icon_path, desc):
    print(f"🖱️ 嘗試點擊：{desc}")
    pos = pyautogui.locateCenterOnScreen(icon_path, confidence=0.85)
    if pos:
        pyautogui.click(pos)
        time.sleep(1.5)
        return True
    else:
        print(f"❌ 找不到 {desc} 圖示：{icon_path}")
        return False

def capture_and_ocr():
    print("📸 擷取畫面中（全螢幕）...")
    image = pyautogui.screenshot()
    image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS)

    os.makedirs(BASE_DIR, exist_ok=True)
    image.save(SCREENSHOT_PATH)
    print(f"🖼️ 圖片已儲存至：{SCREENSHOT_PATH}")

    text = pytesseract.image_to_string(image, lang='chi_tra+eng')
    print("📋 OCR 辨識結果如下：\n", text)
    plus_ones = [line.strip() for line in text.splitlines() if '+1' in line or '＋1' in line]
    return plus_ones

def save_to_db_and_csv(messages):
    if not messages:
        return
    # 儲存到 SQLite
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT UNIQUE,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    for msg in messages:
        c.execute("INSERT OR IGNORE INTO notes (content) VALUES (?)", (msg,))
    conn.commit()
    conn.close()

    # 儲存到 CSV
    with open(CSV_PATH, 'a', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        for msg in messages:
            writer.writerow([msg])
    print(f"💾 已存入資料庫與 {CSV_PATH}，新增筆數：{len(messages)}")

def main():
    if not switch_to_line():
        sys.exit()

    # 自動雙擊群組 ➜ 記事本 ➜ 留言圖示
    if not double_click_icon(GROUP_ICON, "測試用群組圖示"): sys.exit()
    if not double_click_icon(NOTEBOOK_ICON, "記事本圖示"): sys.exit()
    if not single_click_icon(BUBBLE_ICON, "留言圖示"): sys.exit()

    # 截圖並 OCR
    msgs = capture_and_ocr()

    if msgs:
        print("✅ 偵測到 +1 留言如下：")
        for m in msgs:
            print("  -", m)
    else:
        print("⚠️ 沒有偵測到任何 +1 留言")

    save_to_db_and_csv(msgs)

if __name__ == '__main__':
    main()
