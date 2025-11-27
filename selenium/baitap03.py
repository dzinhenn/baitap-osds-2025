from selenium import webdriver
from selenium.webdriver.common.by import By
import time

driver = webdriver.Chrome()

url = "https://en.wikipedia.org/wiki/List of painters by name beginning with %22P%22"
driver.get(url)

time.sleep(2)

ul_tags = driver.find_elements(By.TAG_NAME, "ul")
print(len(ul_tags))

ul_painters = ul_tags[20]

li_tags = ul_painters.find_elements(By.TAG_NAME, "li")

links = [tag.find_element(By.TAG_NAME, "a").get_attribute("href") for tag in li_tags]

titles = [tag.find_element(By.TAG_NAME, "a").get_attribute("title") for tag in li_tags]

for link in links:
    print(link)
    
for title in titles:
    print(title)
    
driver.quit()