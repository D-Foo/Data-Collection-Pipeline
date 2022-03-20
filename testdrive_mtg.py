from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time
import string

driver = webdriver.Firefox()
URL = "https://www.cardmarket.com/en/Magic/Products/Singles/Avacyn-Restored/Avacyn-Angel-of-Hope"
driver.get(URL)
delay = 10
time.sleep(2) # Wait a couple of seconds, so the website doesn't suspect you are a bot

try: 
    WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, '//div[@id="CookiesConsent"]')))
    accept_cookies_button = driver.find_element_by_xpath('//button[@aria-label="Accept All Cookies"]')
    accept_cookies_button.click()
except TimeoutException:
    print("Loading took much time (>" + string(delay) + "s)")
except BaseException as err:
    print(f"Unexpected {err=}, {type(err)=}")
    raise