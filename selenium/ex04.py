from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from getpass import getpass
import time
import sys

# Fix lỗi Unicode khi print
sys.stdout.reconfigure(encoding='utf-8')

# ======= Nhập thông tin đăng nhập =======
email_input = input("Nhập email/SDT Facebook: ")
password_input = getpass("Nhập mật khẩu Facebook: ")

# ======= Cấu hình WebDriver =======

gecko_path = r"D:/codes/Selenium/geckodriver.exe"      # <-- CHẮC CHẮN PHẢI ĐÚNG FILE THẬT

service = Service(gecko_path)

options = webdriver.FirefoxOptions()
options.binary_location = r"C:/Program Files/Mozilla Firefox/firefox.exe"  # <-- Đường dẫn Firefox
options.headless = False  # Cho hiện cửa sổ (không bật headless khi login)

driver = webdriver.Firefox(service=service, options=options)

# ======= Mở trang login Facebook =======
driver.get("https://www.facebook.com/login")

# ======= Điền email =======
email_box = WebDriverWait(driver, 15).until(
    EC.presence_of_element_located((By.ID, "email"))
)
email_box.clear()
email_box.send_keys(email_input)

# ======= Điền mật khẩu =======
password_box = WebDriverWait(driver, 15).until(
    EC.presence_of_element_located((By.ID, "pass"))
)
password_box.clear()
password_box.send_keys(password_input)

# ======= Click login =======
login_button = WebDriverWait(driver, 15).until(
    EC.element_to_be_clickable((By.NAME, "login"))
)
login_button.click()

print("Đang đăng nhập...")

# Đợi xem có bị checkpoint hay login thành công
time.sleep(20)

driver.quit()
