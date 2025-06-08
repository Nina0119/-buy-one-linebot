import pytesseract
import pygetwindow as gw
import pyautogui
import sqlite3
import time
import sys
from PIL import Image

# 設定 Tesseract 路徑
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

DB_NAME = 'line_notes.db'
CONFIDENCE = 0.85  # 圖片辨識信心度

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

def click_image(image_path, action_desc):
    print(f"🔍 嘗試點選「{action_desc}」...")
    location = pyautogui.locateCenterOnScreen(image_path, confidence=CONFIDENCE)
    if location:
        pyautogui.moveTo(location)
        pyautogui.click()
        time.sleep(1)
        return True
    else:
        print(f"❌ 找不到圖片：{action_desc}")
        return False

def open_test_group_and_notebook():
    if not click_image('group_test.png', '測試用群組'):
        sys.exit()
    time.sleep(2)
    if not click_image('notebook_icon.png', '記事本圖示'):
        sys.exit()
    time.sleep(2)

def capture_article_notes_area():
    # 根據解析度調整此區域：x, y, width, height
    region = (400, 200, 500, 600)
    return pyautogui.screenshot(region=region)

def extract_plus_ones_from_image(image):
    text = pytesseract.image_to_string(image, lang='chi_tra+eng')
    print("📋 OCR 辨識內容如下：\n", text)
    plus_ones = [line.strip() for line in text.split('\n') if '+1' in line or '＋1' in line]
    return plus_ones

def save_to_db(messages):
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

def main():
    if not switch_to_line():
        sys.exit()

    open_test_group_and_notebook()

    print("📸 擷取留言畫面中...")
    image = capture_article_notes_area()
    msgs = extract_plus_ones_from_image(image)

    if msgs:
        print("✅ 擷取到 +1 留言：")
        for m in msgs:
            print("  -", m)
    else:
        print("⚠️ 沒有偵測到任何 +1 留言")

    save_to_db(msgs)
    print("💾 存檔完成，共新增筆數：", len(msgs))

if __name__ == '__main__':
    main()
