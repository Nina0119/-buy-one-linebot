import pygetwindow as gw
import pyautogui
import sqlite3
import time
import sys
import os
import csv
from collections import Counter
from PIL import Image
from google.cloud import vision
from google.oauth2 import service_account
import google.generativeai as genai
from dotenv import load_dotenv

# ========== 設定 ==========

BASE_DIR = r'C:\Users\chimou\Desktop\linebot 0608'
GROUP_ICON = os.path.join(BASE_DIR, 'group_test.PNG')
NOTEBOOK_ICON = os.path.join(BASE_DIR, 'notebook_icon.png')
BUBBLE_ICON = os.path.join(BASE_DIR, '0f777bdf-d7c1-4300-b07b-d1f72e7b4fb9.png')
SCREENSHOT_PATH = os.path.join(BASE_DIR, 'screenshot_debug.png')
CSV_PATH = os.path.join(BASE_DIR, 'output.csv')
DB_NAME = 'line_notes.db'

# ========== 功能函數 ==========

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
    print(f"💕 嘗試點擊：{desc}")
    pos = pyautogui.locateCenterOnScreen(icon_path, confidence=0.85)
    if pos:
        pyautogui.doubleClick(pos)
        time.sleep(1.5)
        return True
    else:
        print(f"❌ 找不到 {desc} 圖示：{icon_path}")
        return False

def single_click_icon(icon_path, desc):
    print(f"💕 嘗試點擊：{desc}")
    pos = pyautogui.locateCenterOnScreen(icon_path, confidence=0.85)
    if pos:
        pyautogui.click(pos)
        time.sleep(1.5)
        return True
    else:
        print(f"❌ 找不到 {desc} 圖示：{icon_path}")
        return False

# 替換你服務金鑰的路徑
import os
from google.oauth2 import service_account
load_dotenv()  # 讀取 .env 檔案

VISION_KEY_PATH = os.getenv("GOOGLE_KEY_PATH")

if not VISION_KEY_PATH or not os.path.exists(VISION_KEY_PATH):
    raise FileNotFoundError("❌ 無法找到 vision_key.json，請確認路徑是否正確")

credentials = service_account.Credentials.from_service_account_file(VISION_KEY_PATH)

# 📁 設定基礎資料夾與截圖存檔路徑
BASE_DIR = r'C:\Users\chimou\Desktop\linebot 0608\screenshots'
SCREENSHOT_PATH = os.path.join(BASE_DIR, 'screenshot_debug.png')

# 🔑 替換成你的金鑰檔案路徑
VISION_KEY_PATH = r'C:\Users\chimou\Desktop\linebot 0608\vision_key.json'

def extract_plus_one_messages(lines):
    """
    自訂：提取留言中包含「+1」的使用者名稱
    你可以根據實際格式微調此邏輯
    """
    plus_ones = []
    for i, line in enumerate(lines):
        if "+1" in line:
            # 嘗試抓上面一行當作人名
            if i > 0:
                plus_ones.append(lines[i - 1])
            else:
                plus_ones.append("未知")
    return plus_ones

def capture_and_ocr():
    print("📸 擷取畫面中（全螢幕）...")
    image = pyautogui.screenshot()

    # 儲存圖片
    os.makedirs(BASE_DIR, exist_ok=True)
    image.save(SCREENSHOT_PATH)
    print(f"🖼️ 圖片已儲存至：{SCREENSHOT_PATH}")

    # 建立 Vision API 客戶端
    credentials = service_account.Credentials.from_service_account_file(VISION_KEY_PATH)
    client = vision.ImageAnnotatorClient(credentials=credentials)

    # 讀取圖片並轉成 base64
    with open(SCREENSHOT_PATH, 'rb') as image_file:
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
        print("\n🔍 OCR 切行結果：")
        for line in lines:
            print(" -", line)

        plus_ones = extract_plus_one_messages(lines)
        return plus_ones, lines

    except Exception as e:
        print(f"❌ OCR 發生錯誤：{e}")
        return [], []


def save_to_db_and_csv(messages):
    if not messages:
        return
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

def main():
    if not switch_to_line():
        sys.exit()

    if not double_click_icon(GROUP_ICON, "測試用群組圖示"): sys.exit()
    if not double_click_icon(NOTEBOOK_ICON, "記事本圖示"): sys.exit()
    if not single_click_icon(BUBBLE_ICON, "留言圖示"): sys.exit()

    # 擷取畫面與 OCR
    plus_ones, all_lines = capture_and_ocr()
    print("\n📊 加一名單：", plus_ones)

    # 儲存到 DB 與 CSV
    save_to_db_and_csv(plus_ones)

if __name__ == "__main__":
    main()

