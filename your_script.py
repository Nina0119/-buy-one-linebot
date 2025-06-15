import pytesseract
import pygetwindow as gw
import pyautogui
import sqlite3
import time
import sys
import os
import csv
import re
from collections import Counter
from PIL import Image, ImageEnhance, ImageFilter

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

def extract_plus_one_messages(lines):
    plus_ones = []
    name_candidate = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 嘗試從一行中同時偵測人名與 +1
        match = re.search(r'([A-Za-z一-龥]{2,})\s*(\+1|＋1)', line)
        if match:
            plus_ones.append(f"{match.group(1)} +1")
            name_candidate = None
            continue

        # 若符合人名格式，暫存
        if re.fullmatch(r'[A-Za-z一-龥]{2,}', line):
            name_candidate = line
            continue

        # 若前一行是人名，且本行是 +1
        if name_candidate and re.fullmatch(r'(\+1|＋1)', line):
            plus_ones.append(f"{name_candidate} +1")
            name_candidate = None
            continue

        # 其他情況清除暫存
        name_candidate = None

    return plus_ones

def capture_and_ocr():
    print("📸 擁有畫面中（全螢幕）...")
    original = pyautogui.screenshot()
    os.makedirs(BASE_DIR, exist_ok=True)
    original.save(SCREENSHOT_PATH)
    print(f"🖼️ 圖片已儲存至：{SCREENSHOT_PATH}")

    custom_config = r'--oem 3 --psm 11 -c preserve_interword_spaces=1 tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+１1234567890一二三四五六七八九十王林陳李張黃吳劉楊周徐鄭謝Nina'

    all_lines = []
    all_plus_ones = []

    for i in range(4):
        img = original.copy()
        if i == 0:
            img = img.resize((int(img.width * 2.5), int(img.height * 2.5)), Image.LANCZOS)
        elif i == 1:
            img = img.convert('L').filter(ImageFilter.SHARPEN)
        elif i == 2:
            img = ImageEnhance.Contrast(img).enhance(2.0).convert('L')
        elif i == 3:
            img = img.convert('L').point(lambda x: 0 if x < 130 else 255, '1')

        text = pytesseract.image_to_string(img, lang='chi_tra+eng', config=custom_config)
        print(f"\n🌀 OCR 模式 {i+1} 結果：\n{text}")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        all_lines.extend(lines)
        plus_ones = extract_plus_one_messages(lines)
        all_plus_ones.extend(plus_ones)

    unique_plus_ones = list(set(all_plus_ones))

    print("\n🔍 綜合 OCR 偵測結果：")
    for msg in unique_plus_ones:
        print(" -", msg)

    return unique_plus_ones, all_lines

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

    counter = Counter([msg.split()[0] for msg in messages if len(msg.split()) > 1])
    print("\n📊 個別票數統計：")
    for name, count in counter.items():
        print(f"  - {name}: {count} 票")

def main():
    if not switch_to_line():
        sys.exit()

    if not double_click_icon(GROUP_ICON, "測試用群組圖示"): sys.exit()
    if not double_click_icon(NOTEBOOK_ICON, "記事本圖示"): sys.exit()
    if not single_click_icon(BUBBLE_ICON, "留言圖示"): sys.exit()

    msgs, _ = capture_and_ocr()

    if msgs:
        print("\n✅ 偵測到 +1 留言如下：")
        for m in msgs:
            print("  -", m)
    else:
        print("⚠️ 沒有偵測到任何 +1 留言")

    save_to_db_and_csv(msgs)

if __name__ == '__main__':
    main()
