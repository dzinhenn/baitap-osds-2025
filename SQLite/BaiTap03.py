from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

print(" Đang khởi động Chrome...")
print(" Lần đầu chạy sẽ tự động tải ChromeDriver, hãy đợi...")

try:
    # Tự động cài đặt ChromeDriver - KHÔNG CẦN TẢI THỦ CÔNG!
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    
    driver = webdriver.Chrome(options=options)
    
    # TẠO DATABASE + TABLE SQLite
    db = "longchau_db.sqlite"
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sanpham (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_url TEXT UNIQUE,
        product_name TEXT,
        price TEXT,
        original_price TEXT,
        unit TEXT
    )
    """)
    conn.commit()

    # MỞ TRANG
    print(" Chrome đã mở")
    print(" Đang truy cập trang web...")
    driver.get("https://nhathuoclongchau.com.vn/thuc-pham-chuc-nang/vitamin-khoang-chat")
    time.sleep(5)
    
    # KIỂM TRA VÀ IN RA TẤT CẢ CÁC NÚT TRÊN TRANG
    print("Đang kiểm tra các nút trên trang...")
    try:
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"   Tìm thấy {len(all_buttons)} nút button")
        for btn in all_buttons[:20]:  # Chỉ in 20 nút đầu
            text = btn.text.strip()
            if text and len(text) < 100:
                print(f"   - '{text}'"[:80])
    except:
        pass
    
    # PHƯƠNG PHÁP 1: CUỘN LIÊN TỤC ĐỂ LOAD (INFINITE SCROLL)
    print(" Đang cuộn liên tục để tải sản phẩm (infinite scroll)...")
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    products_count = 0
    no_change_count = 0
    
    for scroll_round in range(100):  # Tối đa 100 vòng cuộn
        # Cuộn xuống cuối trang
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Đếm số sản phẩm hiện tại
        current_products = len(driver.find_elements(By.XPATH, "//button[contains(text(),'Chọn mua')]"))
        
        # Kiểm tra chiều cao mới
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height and current_products == products_count:
            no_change_count += 1
            if no_change_count >= 3:
                print(f"   → Đã cuộn hết, không có sản phẩm mới nữa")
                break
        else:
            no_change_count = 0
            
        if current_products > products_count:
            print(f"   → Vòng {scroll_round + 1}: Đã load được {current_products} sản phẩm (+{current_products - products_count})")
            products_count = current_products
            
        last_height = new_height
        
        # Thử tìm và click nút "Xem thêm" nếu có
        try:
            buttons_to_try = [
                "//button[contains(text(),'Xem thêm')]",
                "//*[contains(text(),'Xem thêm')]",
                "//button[contains(text(),'sản phẩm')]",
                "//*[contains(text(),'sản phẩm')]",
                "//button[contains(text(),'Xem')]",
                "//a[contains(text(),'Xem thêm')]",
                "//div[contains(@class, 'load-more')]//button"
            ]
            
            for xpath in buttons_to_try:
                try:
                    btn = driver.find_element(By.XPATH, xpath)
                    btn_text = btn.text.strip()
                    
                    # Chỉ click nếu text có chứa "Xem thêm"
                    if "Xem thêm" in btn_text or "sản phẩm" in btn_text:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", btn)
                        print(f"    Đã click nút: '{btn_text}'")
                        time.sleep(4)  # Chờ lâu hơn để sản phẩm load
                        break
                except:
                    continue
        except:
            pass
    
    print(f" Hoàn thành cuộn trang, tổng cộng {products_count} sản phẩm")
    
    # Cuộn về đầu trang
    driver.execute_script("window.scrollTo(0, 0)")
    time.sleep(2)

    # TÌM TẤT CẢ SẢN PHẨM
    print(" Đang tìm sản phẩm...")
    
    # Thử nhiều cách tìm button "Chọn mua"
    buttons = []
    try:
        buttons = driver.find_elements(By.XPATH, "//button[contains(text(),'Chọn mua')]")
    except:
        pass
    
    if len(buttons) == 0:
        try:
            buttons = driver.find_elements(By.XPATH, "//button[contains(@class, 'btn')]")
        except:
            pass
    
    total = len(buttons)
    print(f" Tìm thấy {total} sản phẩm")
    
    if total == 0:
        print(" KHÔNG TÌM THẤY SẢN PHẨM NÀO!")
        print(" Đang chụp màn hình để kiểm tra...")
        driver.save_screenshot("debug_screenshot.png")
        print("Đã lưu screenshot vào: debug_screenshot.png")
        print("\n Đang kiểm tra HTML của trang...")
        print(driver.page_source[:500])
        driver.quit()
        conn.close()
        sys.exit(1)
    
    print("="*70)

    # CÀO TỪNG SẢN PHẨM
    success_count = 0
    for index, bt in enumerate(buttons, 1):
        try:
            # Tìm div cha chứa thông tin sản phẩm
            div = bt
            for _ in range(3):
                div = div.find_element(By.XPATH, "./..")

            # Lấy tên sản phẩm
            try:
                name = div.find_element(By.TAG_NAME, 'h3').text
            except:
                name = "Không rõ"

            # Lấy giá
            try:
                price = div.find_element(By.CLASS_NAME, 'text-blue-5').text
            except:
                price = "0"

            # Lấy giá gốc
            try:
                original_price = div.find_element(By.CLASS_NAME, "line-through").text
            except:
                original_price = price

            # Lấy link
            try:
                link = div.find_element(By.TAG_NAME, 'a').get_attribute('href')
            except:
                print(f"  [{index}/{total}]  Không tìm thấy link, bỏ qua")
                continue

            # Lấy unit (đơn vị)
            unit = "Không rõ"
            try:
                # Mở tab mới
                driver.execute_script("window.open(arguments[0]);", link)
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(1.5)

                # Tìm Quy cách
                try:
                    unit = driver.find_element(
                        By.XPATH,
                        "//div[contains(text(),'Quy cách')]/following-sibling::div[1]"
                    ).text
                except:
                    # Fallback: tìm các từ khóa
                    try:
                        unit = driver.find_element(
                            By.XPATH,
                            "//*[contains(text(),'Hộp') or contains(text(),'Chai') or contains(text(),'Tuýp') or contains(text(),'Vỉ')]"
                        ).text
                    except:
                        unit = "Không rõ"

                # Đóng tab và quay lại tab chính
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

            except Exception as e:
                unit = "Không rõ"
                # Đảm bảo quay về tab chính nếu có lỗi
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

            # LƯU VÀO SQLite
            try:
                cursor.execute("""
                INSERT OR IGNORE INTO sanpham(product_url, product_name, price, original_price, unit)
                VALUES (?,?,?,?,?)
                """, (link, name, price, original_price, unit))
                conn.commit()
                
                # Hiển thị tiến độ
                name_display = name[:45] + "..." if len(name) > 45 else name
                print(f"  [{index}/{total}] ✓ {name_display}")
                print(f"           Giá: {price} | Quy cách: {unit}")
                success_count += 1
                
            except Exception as e:
                print(f"  [{index}/{total}]  Lỗi lưu database: {e}")

        except Exception as e:
            print(f"  [{index}/{total}]  Lỗi xử lý sản phẩm: {e}")
            # Đảm bảo quay về tab chính nếu có lỗi
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            continue

    print("="*70)
    print(f" HOÀN THÀNH!")
    print(f" Đã lưu thành công: {success_count}/{total} sản phẩm")
    print(f" Database: {db}")
    print("="*70)

except Exception as e:
    print(f"\n LỖI CHƯƠNG TRÌNH: {e}")
    import traceback
    traceback.print_exc()

finally:
    # ĐÓNG KẾT NỐI
    try:
        driver.quit()
        print(" Đã đóng trình duyệt")
    except:
        pass
    
    try:
        conn.close()
        print(" Đã đóng database")
    except:
        pass