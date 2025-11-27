from pygments.formatters.html import webify
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

driver = webdriver.Chrome()

url = "https://en.wikipedia.org/wiki/List_of_painters_by_name"
driver.get(url)

time.sleep(5)

tags = driver.find_elements(By.TAG_NAME,"a");

links = [tag.get_attribute("href") for tag in tags]

for link in links:
    print(link)
    
driver.quit