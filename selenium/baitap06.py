from pygments.formatters.html import webify
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import pandas as pd
import re

##################################################################
# I. Tai noi chua links va Tao dataframe rong
all_links = []
d = pd.DataFrame({'name':[],'birth':[],'nationality':[]})

#II. Lay ra tat ca duong dan de truy cap den painters
#Khoi tao Webdriver
for i in range(70,71):
    driver= webdriver.Chrome()
    url = "https://en.wikipedia.org/wiki/List_of_painters_by_name_beginning_with_%22"+chr(i)+"%22"
    try:
        
        driver.get(url)
        
        time.sleep(3)
        
        ul_tags = driver.find_elements(By.TAG_NAME,"ul")
        print(len(ul_tags))
        
        ul_painters = ul_tags[20]
        
        li_tags = ul_painters.find_elements(By.TAG_NAME,"li")
        
        links = [tag.find_element(By.TAG_NAME,"a").get_attribute("href") for tag in li_tags]
        for x in links:
            all_links.append(x)
    except:
        print("Error!")
        
    driver.quit()
    
#III. Lay thong tin cua tung hoa si
count = 0;
for link in all_links:
    if (count>3):
        break
    count = count + 1;
    
    print(link)
    try:
        driver = webdriver.Chrome()
        url = link
        driver.get(url)
        
        time.sleep(2)
        
        
        try:
            name = driver.find_element(By.TAG_NAME,"hl").text
        except:
            name =""
        
        try: 
            birth_element = driver.find_element(By.XPATH,"//th[text()='Born']/following-sibling::td")
            birth = birth_element.text
            birth = re.findall(r'[0-9]{1,2}+\s+[A-Za-z]+\s+[0-9]{4}',birth)[0]
        except:
            birth=""
        
        
    #lay ngay mat
        try:
            nationality_element = driver.find_element(By.XPATH,"//th[text()='Nationality']/following-sibling::td")
            nationality = nationality_element.text
        except:
            nationality=""
        
        painter = {'name':name,'birth':birth,'nationality':nationality}
        
        painter_df = pd.DataFrame([painter])
        
        d = pd.concat([d,painter_df], ignore_index=True)
        
        driver.quit()
        
    except:
        pass
    
#IV. In thong tin
print(d)

file_name = 'Painter.xlsx'

d.to_excel(file_name)
print('DataFrame is written to Excel File successfully')  