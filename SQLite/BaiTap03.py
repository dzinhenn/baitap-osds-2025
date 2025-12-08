# longchau_scrape_sqlite.py
import os
import sqlite3
import time
import re
import sys
from datetime import datetime
import pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# ========== CẤU HÌNH ==========
USE_CHROME = True           # True: dùng ChromeDriver, False: dùng Firefox(geckodriver)
CHROME_DRIVER_PATH = None   # None nếu ChromeDriver có trên PATH, hoặc đặt đường dẫn đầy đủ
GECKO_PATH = r"C:/User/admin/baitap-osds-2025/SQLite/geckodriver.exe"  # chỉnh nếu dùng gecko
HEADLESS = False            # True nếu muốn chạy ẩn

DB_FILE = "longchau_db.sqlite"
TABLE_NAME = "products_longchau"

# URL danh mục (bạn có thể đổi sang mục khác)
START_URL = "https://nhathuoclongchau.com.vn/thuc-pham-chuc-nang/vitamin-khoang-chat"

# Số sản phẩm tối thiểu muốn cào (cố gắng đạt)
TARGET_COUNT = 50

# Xoá data cũ trước khi cào? (True = xóa bảng cũ)
CLEAR_OLD_DATA = True

# Thời gian chờ/tiêm (tăng nếu mạng chậm)
SHORT_WAIT = 0.8
LONG_WAIT = 2.0

# ========== HỖ TRỢ DRIVER ==========
def create_driver():
    """Tạo webdriver: thử Chrome trước nếu USE_CHROME True, ngược lại dùng Firefox.
       Trả về driver (phải được đóng bằng driver.quit())."""
    if USE_CHROME:
        try:
            from selenium.webdriver.chrome.service import Service as ChromeService
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            opts = ChromeOptions()
            if HEADLESS:
                opts.add_argument("--headless=new")
            if CHROME_DRIVER_PATH:
                service = ChromeService(CHROME_DRIVER_PATH)
                driver = webdriver.Chrome(service=service, options=opts)
            else:
                driver = webdriver.Chrome(options=opts)  # yêu cầu chromedriver trên PATH
            return driver
        except Exception as e:
            print("Không thể khởi tạo Chrome driver:", e)
            print("Thử chuyển sang Firefox...")
    # Firefox fallback
    try:
        from selenium.webdriver.firefox.service import Service as GeckoService
        from selenium.webdriver.firefox.options import Options as FFOptions
        opts = FFOptions()
        if HEADLESS:
            opts.headless = True
        service = GeckoService(GECKO_PATH) if GECKO_PATH else None
        driver = webdriver.Firefox(service=service, options=opts)
        return driver
    except Exception as e:
        print("Không thể khởi tạo Firefox driver:", e)
        raise RuntimeError("Không tìm thấy driver phù hợp. Cài ChromeDriver/GeckoDriver và thử lại.")

# ========== HỖ TRỢ XỬ LÝ GIÁ/ĐƠN VỊ ==========
def parse_price(price_text):
    """Nhận text giá (ví dụ '390.000₫', '390.000 đ', '390.000đ/hộp') 
       Trả về tuple (price_int_in_VND or None, display_string, unit_guess).
       price_int là int như 390000."""
    if not price_text:
        return None, "", ""
    txt = price_text.strip()
    # chuẩn hoá kiểu: chuyển dấu non-breaking, thay chữ, xóa chữ 'đ', 'VNĐ'
    txt = txt.replace('\xa0', ' ')
    # tách unit nếu có sau dấu '/'
    unit = ""
    if '/' in txt:
        parts = txt.split('/')
        txt_price_part = parts[0]
        unit = parts[1].strip()
    else:
        txt_price_part = txt
    # kéo ra chuỗi số
    nums = re.findall(r'[\d\.\,]+', txt_price_part)
    if not nums:
        return None, price_text, unit
    # nối và loại bỏ dấu chấm/phẩy
    num = nums[0].replace('.', '').replace(',', '')
    try:
        price_int = int(num)
    except:
        try:
            price_int = int(float(num))
        except:
            price_int = None
    # tạo display hợp lệ: 390.000đ/hộp
    display = ""
    if price_int is not None:
        s = f"{price_int:,}".replace(',', '.')  # 390.000
        display = f"{s}đ" + (f"/{unit}" if unit else "")
    else:
        display = price_text
    return price_int, display, unit

# ========== SETUP DB ==========
def init_db(db_file=DB_FILE, clear_old=False):
    if clear_old and os.path.exists(db_file):
        os.remove(db_file)
        print("Đã xóa file DB cũ:", db_file)
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        product_url TEXT PRIMARY KEY,
        product_id TEXT,
        product_name TEXT,
        price INTEGER,
        price_display TEXT,
        original_price INTEGER,
        original_price_display TEXT,
        unit TEXT,
        scraped_at TEXT
    );
    """
    cur.execute(create_sql)
    conn.commit()
    return conn, cur

# ========== CHÈN LƯU NGAY TỨC THỜI ==========
def upsert_product(cur, conn, item):
    """
    item = {
      'product_url':..., 'product_id':..., 'product_name':..., 
      'price': int or None, 'price_display':..., 'original_price':..., 'original_price_display':..., 'unit':...
    }
    Dùng INSERT OR REPLACE để cập nhật nếu đã có.
    """
    now = datetime.utcnow().isoformat()
    sql = f"""
    INSERT OR REPLACE INTO {TABLE_NAME}
      (product_url, product_id, product_name, price, price_display, original_price, original_price_display, unit, scraped_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cur.execute(sql, (
        item.get('product_url'),
        item.get('product_id'),
        item.get('product_name'),
        item.get('price'),
        item.get('price_display'),
        item.get('original_price'),
        item.get('original_price_display'),
        item.get('unit'),
        now
    ))
    conn.commit()

# ========== SCRAPING LOGIC ==========
def scrape_category(url, target_count=TARGET_COUNT):
    driver = create_driver()
    try:
        driver.get(url)
        time.sleep(LONG_WAIT)

        # cố gắng click "Xem thêm" nhiều lần cho đầy sản phẩm (nếu có)
        for attempt in range(10):
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                clicked = False
                for btn in buttons:
                    txt = (btn.text or "").strip()
                    if "Xem thêm" in txt or "xem thêm" in txt or "Xem thêm sản phẩm" in txt:
                        try:
                            btn.click()
                            clicked = True
                            time.sleep(1.0)
                            break
                        except:
                            pass
                if not clicked:
                    # cuộn xuống để load lazy
                    body = driver.find_element(By.TAG_NAME, "body")
                    body.send_keys(Keys.END)
                    time.sleep(1.0)
                # kiểm tra số lượng thẻ sản phẩm hiện có
                pro_cards = driver.find_elements(By.XPATH, "//article | //div[contains(@class,'product-card') or contains(@class,'product-item') or contains(@class,'product')]")
                if len(pro_cards) >= target_count:
                    break
            except Exception as e:
                # tránh dừng khi 1 lần fail
                #print("Attempt click error:", e)
                time.sleep(1.0)

        # Cuộn sâu xuống từ từ để load hết
        for _ in range(20):
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
            time.sleep(0.2)

        # ------------- Lấy các thẻ liên quan tới sản phẩm -------------
        # Cách lấy: tìm các nút "Chọn mua" (theo code bạn gửi), rồi leo lên cha để lấy thông tin
        choose_buttons = driver.find_elements(By.XPATH, "//button[text()[normalize-space()='Chọn mua']]")
        print("Tìm thấy nút 'Chọn mua':", len(choose_buttons))

        items = []
        for idx, bt in enumerate(choose_buttons):
            try:
                # leo lên cha để tìm khung sản phẩm
                parent = bt
                for _ in range(4):
                    parent = parent.find_element(By.XPATH, "./..")
                # từ parent tìm tên (h3), link (a), giá (class text-blue-5), original price nếu có
                try:
                    name = parent.find_element(By.TAG_NAME, "h3").text.strip()
                except:
                    name = ""
                # link: tìm thẻ a trong parent
                try:
                    a = parent.find_element(By.TAG_NAME, "a")
                    product_url = a.get_attribute("href")
                except:
                    product_url = ""
                # giá hiện tại
                try:
                    price_text = parent.find_element(By.CLASS_NAME, "text-blue-5").text.strip()
                except:
                    # fallback tìm theo phần tử chứa 'đ'
                    all_texts = parent.text
                    price_text = ""
                    m = re.search(r'[\d\.\,]+\s*đ', all_texts)
                    if m:
                        price_text = m.group(0)

                # original price: tìm phần có gạch ngang hoặc class 'line-through'
                original_price_text = ""
                try:
                    orig = parent.find_element(By.XPATH, ".//span[contains(@class,'line-through') or contains(@class,'text-gray') or contains(@class,'text-muted')]")
                    original_price_text = orig.text.strip()
                except:
                    # try other fallback
                    try:
                        op = parent.find_element(By.XPATH, ".//del")
                        original_price_text = op.text.strip()
                    except:
                        original_price_text = ""

                # parse price
                price_int, price_display, unit_from_price = parse_price(price_text)
                orig_int, orig_display, unit_from_orig = parse_price(original_price_text)
                # guess unit from name if not found
                unit = unit_from_price or unit_from_orig or ""
                # guess product_id from URL if present (like id=123)
                product_id = ""
                if product_url:
                    m = re.search(r'(\d{4,})', product_url)
                    if m:
                        product_id = m.group(1)
                # create item
                item = {
                    "product_url": product_url,
                    "product_id": product_id,
                    "product_name": name,
                    "price": price_int,
                    "price_display": price_display,
                    "original_price": orig_int,
                    "original_price_display": orig_display,
                    "unit": unit
                }
                items.append(item)
            except Exception as e:
                # skip problematic card
                #print("skip card err:", e)
                continue

        return items
    finally:
        try:
            driver.quit()
        except:
            pass

# ========== MAIN ==========
if __name__ == "__main__":
    conn, cur = init_db(DB_FILE, clear_old=CLEAR_OLD_DATA)
    print("Đã tạo/ở kết nối DB:", DB_FILE)

    # 1) Cào danh mục
    print("Bắt đầu cào trang:", START_URL)
    scraped_items = scrape_category(START_URL, target_count=TARGET_COUNT)
    print("Số item thu thập được (lần 1):", len(scraped_items))

    # 2) LƯU TỨC THỜI MỖI ITEM
    for it in scraped_items:
        if not it.get("product_url"):
            # bỏ qua nếu không có URL - vì ta dùng URL làm khoá chính
            continue
        upsert_product(cur, conn, it)
        print("Lưu:", it.get("product_name")[:60], "-", it.get("price_display"), "- unit:", it.get("unit"))

    # Nếu chưa đủ items, có thể thông báo
    cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
    total = cur.fetchone()[0]
    print("Tổng bản ghi hiện tại trong DB:", total)

    # ========== PHẦN TRUY VẤN (ít nhất 15 truy vấn) ==========
    print("\n--- BẮT ĐẦU TRUY VẤN ---\n")
    queries = []

    # 1. Kiểm tra trùng lặp theo product_url
    queries.append(("Duplicate URLs (should be 0):",
        f"SELECT product_url, COUNT(*) cnt FROM {TABLE_NAME} GROUP BY product_url HAVING cnt>1;"))

    # 2. Duplicate by product_name
    queries.append(("Duplicate names:",
        f"SELECT product_name, COUNT(*) cnt FROM {TABLE_NAME} GROUP BY product_name HAVING cnt>1 ORDER BY cnt DESC;"))

    # 3. Missing price (NULL or 0)
    queries.append(("Missing or zero price:",
        f"SELECT * FROM {TABLE_NAME} WHERE price IS NULL OR price=0 LIMIT 50;"))

    # 4. price > original_price (bất thường)
    queries.append(("Price > original_price (weird):",
        f"SELECT product_name, price, original_price, product_url FROM {TABLE_NAME} WHERE price IS NOT NULL AND original_price IS NOT NULL AND price>original_price LIMIT 50;"))

    # 5. Unique units
    queries.append(("Unique units:",
        f"SELECT DISTINCT unit FROM {TABLE_NAME};"))

    # 6. Total count
    queries.append(("Total records:",
        f"SELECT COUNT(*) FROM {TABLE_NAME};"))

    # 7. Top 10 biggest absolute discount (original_price - price)
    queries.append(("Top 10 biggest discounts (absolute):",
        f"SELECT product_name, original_price, price, (original_price - price) as diff FROM {TABLE_NAME} WHERE original_price IS NOT NULL AND price IS NOT NULL ORDER BY diff DESC LIMIT 10;"))

    # 8. Most expensive product
    queries.append(("Most expensive product:",
        f"SELECT product_name, price, product_url FROM {TABLE_NAME} WHERE price IS NOT NULL ORDER BY price DESC LIMIT 1;"))

    # 9. Count per unit
    queries.append(("Count per unit:",
        f"SELECT unit, COUNT(*) FROM {TABLE_NAME} GROUP BY unit ORDER BY COUNT(*) DESC;"))

    # 10. Products containing 'Vitamin C' (case-insensitive)
    queries.append(("Products with 'Vitamin C':",
        f"SELECT * FROM {TABLE_NAME} WHERE LOWER(product_name) LIKE '%vitamin c%' OR LOWER(product_name) LIKE '%vitamin-c%' LIMIT 50;"))

    # 11. Price between 100k and 200k
    queries.append(("Price between 100k and 200k:",
        f"SELECT product_name, price, product_url FROM {TABLE_NAME} WHERE price BETWEEN 100000 AND 200000 LIMIT 50;"))

    # 12. Sort by price asc
    queries.append(("All products sorted by price ASC (top 20):",
        f"SELECT product_name, price FROM {TABLE_NAME} WHERE price IS NOT NULL ORDER BY price ASC LIMIT 20;"))

    # 13. Percent discount and top 5
    queries.append(("Top 5 percent discounts:",
        f"SELECT product_name, price, original_price, (original_price - price)*1.0 / original_price as pct FROM {TABLE_NAME} WHERE original_price IS NOT NULL AND original_price>0 AND price IS NOT NULL ORDER BY pct DESC LIMIT 5;"))

    # 14. Delete duplicates keep one (CTE) - show command but DO NOT execute delete automatically
    queries.append(("SQL to delete duplicates (keeps one):",
        f"""WITH duplicates AS (
            SELECT product_url, ROW_NUMBER() OVER (PARTITION BY product_url ORDER BY scraped_at DESC) rn
            FROM {TABLE_NAME}
        )
        DELETE FROM {TABLE_NAME} WHERE product_url IN (SELECT product_url FROM duplicates WHERE rn>1);
        """))

    # 15. Price groups (<50k, 50k-100k, >100k)
    queries.append(("Price groups counts:",
        f"SELECT CASE WHEN price<50000 THEN 'under_50k' WHEN price BETWEEN 50000 AND 100000 THEN '50k_100k' WHEN price>100000 THEN 'over_100k' ELSE 'unknown' END as grp, COUNT(*) FROM {TABLE_NAME} GROUP BY grp;"))

    # 16. URLs null or empty
    queries.append(("URL NULL or empty:",
        f"SELECT * FROM {TABLE_NAME} WHERE product_url IS NULL OR TRIM(product_url)='';"))

    # Thực thi và in
    for title, q in queries:
        print(">>", title)
        try:
            cur.execute(q)
            rows = cur.fetchall()
            if len(rows) == 0:
                print("  (No rows)")
            else:
                # in tối đa 10 dòng để không quá dài
                for r in rows[:20]:
                    print("  ", r)
            print("")
        except Exception as e:
            print("  Lỗi khi chạy query:", e)
            print("  Query text:", q)
            print("")

    # đóng kết nối
    conn.close()
    print("Hoàn tất. DB lưu tại:", DB_FILE)
