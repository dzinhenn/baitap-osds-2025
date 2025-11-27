from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import pandas as pd
import re

# Tao dataframe rong
d = pd.DataFrame({'name': [], 'birth': [], 'death': [], 'nationality': []})

# Khoi tao webdriver
driver = webdriver.Chrome()

# URL dung
url = "https://en.wikipedia.org/wiki/Edvard_Munch"
driver.get(url)

time.sleep(2)

# 1. Lay Ten
try:
    name = driver.find_element(By.TAG_NAME, "h1").text
except Exception as e:
    # SUA LOI: Viet khong dau
    print(f"Loi lay ten: {e}")
    name = ""

# 2. Lay Ngay sinh
try:
    # Dung contains de tim kiem linh hoat hon
    birth_element = driver.find_element(By.XPATH, "//th[contains(text(), 'Born')]/following-sibling::td")
    birth_text = birth_element.text
    # Regex lay ngay thang
    birth = re.findall(r'[0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4}', birth_text)[0]
except Exception as e:
    print(f"Loi lay ngay sinh: {e}")
    birth = ""

# 3. Lay Ngay mat
try:
    death_element = driver.find_element(By.XPATH, "//th[contains(text(), 'Died')]/following-sibling::td")
    death_text = death_element.text
    death = re.findall(r'[0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4}', death_text)[0]
except Exception as e:
    print(f"Loi lay ngay mat: {e}")
    death = ""

# 4. Lay Quoc tich
try:
    # Su dung contains(., 'Nationality') de tim bat ky th nao chua chu Nationality
    nationality_element = driver.find_element(By.XPATH, "//th[contains(., 'Nationality')]/following-sibling::td")
    nationality = nationality_element.text
except Exception as e:
    
    print("Khong tim thay Quoc tich") 
    nationality = ""

driver.quit()

# Tao dictionary
painter = {'name': name, 'birth': birth, 'death': death, 'nationality': nationality}
painter_df = pd.DataFrame([painter])

d = pd.concat([d, painter_df], ignore_index=True)

print("\nKET QUA:")
print(d)