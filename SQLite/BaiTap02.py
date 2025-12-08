from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import pandas as pd
import re
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
painters_df = pd.DataFrame(columns=['name', 'birth', 'death', 'nationality'])

driver = webdriver.Chrome()
url = "https://en.wikipedia.org/wiki/List_of_painters_by_name_beginning_with_%22F%22"
driver.get(url)
time.sleep(3)

ul_tags = driver.find_elements(By.TAG_NAME, "ul")
ul_painters = None
for ul in ul_tags:
    if "Fragonard" in ul.text:
        ul_painters = ul
        break

if ul_painters is None:
    print("Could not find the painters list.")
    driver.quit()
    exit()

li_tags = ul_painters.find_elements(By.TAG_NAME, "li")
all_links = []
for li in li_tags:
    try:
        all_links.append(li.find_element(By.TAG_NAME, "a").get_attribute("href"))
    except:
        continue

for count, link in enumerate(all_links):
    if count >= 100:
        break

    driver.get(link)
    time.sleep(2)

    # NAME
    try:
        name = driver.find_element(By.TAG_NAME, "h1").text
    except:
        name = ""

    # BIRTH
    try:
        birth_text = driver.find_element(By.XPATH, "//th[text()='Born']/following-sibling::td").text
        birth_match = re.findall(r'\d{1,2}\s[A-Za-z]+\s\d{4}|\d{4}', birth_text)
        birth = birth_match[0] if birth_match else ""
    except:
        birth = ""

    # DEATH
    try:
        death_text = driver.find_element(By.XPATH, "//th[text()='Died']/following-sibling::td").text
        death_match = re.findall(r'\d{1,2}\s[A-Za-z]+\s\d{4}|\d{4}', death_text)
        death = death_match[0] if death_match else ""
    except:
        death = ""

    # NATIONALITY
    try:
        birth_td = driver.find_element(By.XPATH, "//th[text()='Born']/following-sibling::td")
        birth_text = birth_td.text.strip()
        if ',' in birth_text:
            citizen = birth_text.split(',')[-1].strip()
        else:
            parts = birth_text.split()
            citizen = parts[-1] if parts else "Unknown"
    except:
        citizen = "Unknown"

    painters_df.loc[len(painters_df)] = [name, birth, death, citizen]

driver.quit()

# KẾT NỐI DATABASE
conn = sqlite3.connect("painters.db")
cursor = conn.cursor()

# XÓA BẢNG CŨ NẾU TỒN TẠI (để tạo lại với cấu trúc mới)
cursor.execute("DROP TABLE IF EXISTS painters")

# TẠO BẢNG MỚI
cursor.execute("""
CREATE TABLE painters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    birth TEXT,
    death TEXT,
    nationality TEXT
)
""")

# CHÈN DỮ LIỆU
sql_insert = """
INSERT INTO painters (name, birth, death, nationality)
VALUES (?, ?, ?, ?)
"""

cursor.executemany(sql_insert, painters_df.values.tolist())
conn.commit()

print("✅ Đã lưu dữ liệu vào database!")
print("="*70)

# A. THỐNG KÊ TOÀN CỤC
print("\n📊 THỐNG KÊ TOÀN CỤC")
print("="*70)

# 1. Tổng số họa sĩ
cursor.execute("SELECT COUNT(*) FROM painters")
print(f"1. Tổng số họa sĩ: {cursor.fetchone()[0]}")

# 2. 5 dòng đầu tiên
print("\n2. 5 dòng dữ liệu đầu tiên:")
cursor.execute("SELECT * FROM painters LIMIT 5")
for row in cursor.fetchall():
    print(f"   {row}")

# 3. Các quốc tịch
print("\n3. Danh sách quốc tịch:")
cursor.execute("SELECT DISTINCT nationality FROM painters")
for row in cursor.fetchall():
    print(f"   - {row[0]}")

# 4. Họa sĩ tên bắt đầu bằng F
cursor.execute("SELECT COUNT(*) FROM painters WHERE name LIKE 'F%'")
print(f"\n4. Số họa sĩ có tên bắt đầu bằng chữ F: {cursor.fetchone()[0]}")

# 5. Họa sĩ không phải người Pháp
print("\n5. Họa sĩ không phải người Pháp:")
cursor.execute("SELECT name, nationality FROM painters WHERE nationality != 'French'")
for row in cursor.fetchall():
    print(f"   - {row[0]} ({row[1]})")

# 6. Họa sĩ không có quốc tịch
print("\n6. Họa sĩ không có thông tin quốc tịch:")
cursor.execute("SELECT name FROM painters WHERE nationality IS NULL OR nationality = '' OR nationality = 'Unknown'")
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f"   - {row[0]}")
else:
    print("   (Không có)")

# 7. Họa sĩ có cả năm sinh và năm mất
print("\n7. Họa sĩ có cả năm sinh và năm mất:")
cursor.execute("""
SELECT name, birth, death FROM painters
WHERE birth IS NOT NULL AND birth != '' 
AND death IS NOT NULL AND death != ''
""")
for row in cursor.fetchall():
    print(f"   - {row[0]} ({row[1]} - {row[2]})")

# 8. Tên chứa 'Fales'
print("\n8. Họa sĩ có tên chứa 'Fales':")
cursor.execute("SELECT name FROM painters WHERE name LIKE '%Fales%'")
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f"   - {row[0]}")
else:
    print("   (Không tìm thấy)")

# 9. Sắp xếp theo tên A-Z
print("\n9. Họa sĩ sắp xếp theo tên A-Z:")
cursor.execute("SELECT name FROM painters ORDER BY name ASC")
for row in cursor.fetchall():
    print(f"   - {row[0]}")

# 10. Thống kê theo quốc tịch
print("\n10. Thống kê số họa sĩ theo quốc tịch:")
cursor.execute("""
SELECT nationality, COUNT(*) 
FROM painters
GROUP BY nationality
ORDER BY COUNT(*) DESC
""")
for row in cursor.fetchall():
    print(f"   - {row[0]}: {row[1]} họa sĩ")

print("\n" + "="*70)
print("✅ HOÀN THÀNH!")

conn.close()