import sqlite3

conn = sqlite3.connect("painters.db")
cursor = conn.cursor()

# Hãy viết dấu nháy dính liền hoặc cùng dòng để tránh lỗi
query = """
SELECT * FROM painters 
WHERE nationality = 'French' 
ORDER BY name ASC
"""

# Thực thi
cursor.execute(query)

# Lấy kết quả
results = cursor.fetchall()

print(f"--- Tìm thấy {len(results)} kết quả ---")
for row in results:
    print(row)

conn.close()