from selenium import webdriver
from selenium.webdriver.common.by import By
import time

#tao 1 driver de bat dau dieu khien
driver = webdriver.Chrome()
driver.maximize_window()
#Mo mot trang web
driver.get('https://gomotungkinh.com/')
time.sleep(5)

try:
    while True:
        driver.find_element(By.ID,'bonk').click()
        time.sleep(1)
except:
    driver.quit()
    
