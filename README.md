# Data Collection Project

> An automated webscraping project to track prices of Magic the Gathering cards on www.cardmarket.com, could be applied to any other website to scrape data from. Makes us of Selenium, Geckodriver

## Creating a URL list and piloting an automated browser

- Creating a URL List

We can access data in .json format containing all the raw card details we need from https://mtgjson.com/. We can download json of a set of cards from https://mtgjson.com/downloads/all-sets/ (Sets are collections of cards released together ~300 cards contained in a set). By parsing the json of a set we can access and save the names of individual cards to a .txt file with the raw card names of the cards we want to find on cardmarket. We then format the raw names into the form they take on cardmarket's urls.


```python
#Convert name to url syntax
for name in card_namelist:
    name = name.replace(" // ", '-')  #Replace the " // " substring with a hyphen
    name = name.translate({ord(c):None for c in "',"}) #Remove any apostrophes or commas in the string
    name = name.replace(' ', '-')  #Replace any spaces with hyphens
    self.formatted_card_list.append(name)
```

- Controlling a browser with Selenium

We can initialise and pilot a firefox browser window using [Selenium](https://www.selenium.dev/documentation/webdriver/) and [Geckodriver](https://github.com/mozilla/geckodriver/releases). To start with we request the base url of the website www.cardmarket.com so we can accept cookies for the website. We wait until the cookies consent window appears, then find the accept cookies button using xpaths then click to accept cookies. 

We can find the xpath of the accept cookies button by inspecting it and examining where the button is contained in the HTML. The button is contained in the div with id="Cookies Consent" so we wait until it has loaded in the browser; then find the button with it's xpath then click it. 


```python
try: 
    WebDriverWait(self.driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//div[@id="CookiesConsent"]')))
    accept_cookies_button = self.driver.find_element_by_xpath('//button[@aria-label="Accept All Cookies"]')
    accept_cookies_button.click()
except TimeoutException:
    print("Loading took much time (>" + string(self.delay) + "s)")

```

Cookies Pop Up | Accepted Cookies!
:-------------------------:|:-------------------------:
![automated_no_cookies_40](https://user-images.githubusercontent.com/36233522/159569096-bb9e6284-db9a-4178-99f8-81f380a2d7b7.png)  |  ![automated_cookies_40](https://user-images.githubusercontent.com/36233522/159569109-04fc6134-ec25-4c02-b6c6-ef2fc4e869c2.png)

After accepting cookies we can iterate through our url list and access each webpage associated with each card name in our list.

```python
  #Scrape rest of data from urls generated from target list data
  #Url
  self.url_base = target_url  #"https://www.cardmarket.com"
  self.url_mtg_section = "/en/Magic/Products/Singles/"
  self.url_set_name = set_name #"Kamigawa-Neon-Dynasty"
  url_head = self.url_base + self.url_mtg_section + self.url_set_name + "/"
  for c in self.formatted_card_list:
    final_url = url_head + c  #Example: https://www.cardmarket.com/en/Magic/Products/Singles/Kamigawa-Neon-Dynasty/Ancestral-Katana
    self.scrape(final_url)
```

