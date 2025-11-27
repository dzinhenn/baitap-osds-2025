from pygments. formatters.html import webify 
from selenium import webdriver 
from selenium.webdriver.common.by import By 
import time
import pandas as pd 
import re
# Tao dataframe rong
d = pd. DataFrame ({'name': [], 'birth':[], 'death': [], 'nationality':[]})
# Khoi tao webdriver
driver = webdriver. Chrome ()
# Mo trang
url = "https://en.wikipedia.org/wiki/Edvard_Murch"
driver.get (url)

# Doi 2 giay
time. sleep (2)

try:
    name = driver. find_element (By. TAG_NAME, "hi"). text
except:
    name = ""
# Lay ngay sinh
try:
    birth_element = driver. find_element(By.XPATH, "//th[text ()='Born')/following-sibling: :td")
    birth = birth_element.text
    birth = re.findall (r' [0-9]{1,2}+\s+[A-Za-z]+\s+[0-9]{4}', birth) [0] # regex
except:
    birth = ""
# Lay ngay mat
try:
    death_element = driver.find_element(By.XPATH, "//th[text () ='Died']/following-sibling:: td")
    death = death_element.text
    death = re.findall (r' [0-9] {1,2}+\s+[A-Za-z]+\s+[0-9] (4)', death)[0]
except:
    death =""
#Lay ngay mat
try:
    nationality_element = driver. find_element (By. XPATH, "//th[text () = 'Nationality')/following-sibling::td")
    nationality = nationality_element. text
except:
    nationality = ""
    
painter = {'name' : name,'birth': birth, 'death': death,'nationality':nationality}

painter_df = pd.DataFrame([painter])

d = pd.concat([d,painter_df], ignore_index=True)

print(d)

driver.quit()